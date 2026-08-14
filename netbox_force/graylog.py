"""
GELF transport towards Graylog.

Design constraints, in order of importance:

1. A Graylog outage must never slow NetBox down. emit() only puts a dict on a
   bounded in-memory queue and returns. All socket work happens on a background
   daemon thread with hard timeouts.
2. The queue is bounded. A queue that fills faster than it drains would grow
   until the worker process dies, and the events lost would be the newest ones.
   Once full, new events are dropped and counted, and the counter is reported
   on the settings page.
3. Message text is always English. Graylog alert queries match on these strings;
   translating them would silently break every alert the moment the UI language
   is changed.

The sender is process-local. Under uwsgi each worker keeps its own queue and
thread, started lazily on first use — that is after fork, which is the only
point at which starting a thread is safe.
"""

import json
import logging
import queue
import socket
import ssl
import struct
import threading
import time
from urllib.request import Request, urlopen

logger = logging.getLogger('netbox.plugins.netbox_force')

# Syslog severities, the subset that is meaningful for audit events.
LEVEL_EMERGENCY = 0
LEVEL_ALERT = 1
LEVEL_CRITICAL = 2
LEVEL_ERROR = 3
LEVEL_WARNING = 4
LEVEL_NOTICE = 5
LEVEL_INFO = 6
LEVEL_DEBUG = 7

GELF_VERSION = '1.1'

# Safe payload size for a single UDP datagram on a 1500-byte MTU link.
_UDP_CHUNK_SIZE = 1420
_GELF_CHUNK_MAGIC = b'\x1e\x0f'
_MAX_UDP_CHUNKS = 128

_QUEUE_MAXSIZE = 2000
_TCP_RECONNECT_BACKOFF = 5.0

# Field values are truncated before serialisation. Graylog indexes these; a
# 50 KB object repr in a log line helps nobody and blows past the UDP limit.
_MAX_FIELD_LENGTH = 512
_MAX_MESSAGE_LENGTH = 1024


class GraylogError(Exception):
    """Raised by send_now() so the test button can report a real reason."""

    def __init__(self, code, detail=''):
        super().__init__(code)
        self.code = code
        self.detail = detail


def default_source_name():
    try:
        return socket.gethostname() or 'netbox'
    except Exception:
        return 'netbox'


def _truncate(value, limit=_MAX_FIELD_LENGTH):
    text = str(value)
    return text if len(text) <= limit else text[:limit - 1] + '…'


def build_gelf(source, short_message, level=LEVEL_INFO, timestamp=None, **fields):
    """
    Assemble a GELF 1.1 payload.

    Additional fields are prefixed with an underscore as the spec requires.
    Empty values are dropped rather than sent as empty strings, so Graylog
    search results stay readable.
    """
    payload = {
        'version': GELF_VERSION,
        'host': source or default_source_name(),
        'short_message': _truncate(short_message, _MAX_MESSAGE_LENGTH),
        'level': int(level),
        'timestamp': float(timestamp if timestamp is not None else time.time()),
    }
    for key, value in fields.items():
        if value is None or value == '':
            continue
        name = key if key.startswith('_') else '_' + key
        if name == '_id':
            # Reserved by the GELF spec — Graylog rejects the whole message.
            name = '_object_id'
        if isinstance(value, bool):
            payload[name] = 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            payload[name] = value
        else:
            payload[name] = _truncate(value)
    return payload


def _serialise(payload):
    return json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')


def _udp_chunks(data):
    """
    Split an oversized datagram per the GELF chunked-message format.

    Returns a list of datagrams ready to send. Messages that fit are returned
    unchanged so the common case carries no overhead.
    """
    if len(data) <= _UDP_CHUNK_SIZE:
        return [data]

    count = (len(data) + _UDP_CHUNK_SIZE - 1) // _UDP_CHUNK_SIZE
    if count > _MAX_UDP_CHUNKS:
        raise GraylogError('too_large', f'{len(data)} bytes')

    message_id = struct.pack('>Q', int(time.time() * 1000) & 0xFFFFFFFFFFFFFFFF)
    chunks = []
    for index in range(count):
        body = data[index * _UDP_CHUNK_SIZE:(index + 1) * _UDP_CHUNK_SIZE]
        chunks.append(_GELF_CHUNK_MAGIC + message_id
                      + bytes([index, count]) + body)
    return chunks


class GelfSender:
    """
    One queue, one worker thread, one connection. Instantiated once per process
    via get_sender().
    """

    def __init__(self):
        self._queue = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        self._worker = None
        self._lock = threading.Lock()
        self._tcp_socket = None
        self._tcp_config = None
        self._next_retry = 0.0
        self.dropped = 0
        self.sent = 0
        self.failed = 0

    # -- public API ------------------------------------------------------

    def emit(self, config, payload):
        """
        Hand a prepared GELF payload to the worker. Never blocks, never raises.
        """
        try:
            self._queue.put_nowait((config, payload))
        except queue.Full:
            self.dropped += 1
            if self.dropped == 1 or self.dropped % 500 == 0:
                logger.warning(
                    'netbox_force: Graylog queue full, %d event(s) dropped',
                    self.dropped)
            return False
        self._ensure_worker()
        return True

    def stats(self):
        return {
            'queued': self._queue.qsize(),
            'sent': self.sent,
            'failed': self.failed,
            'dropped': self.dropped,
        }

    # -- worker ----------------------------------------------------------

    def _ensure_worker(self):
        if self._worker is not None and self._worker.is_alive():
            return
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker = threading.Thread(
                target=self._run, name='netbox-force-graylog', daemon=True)
            self._worker.start()

    def _run(self):
        while True:
            try:
                config, payload = self._queue.get()
            except Exception:
                return
            try:
                self._deliver(config, payload)
                self.sent += 1
            except Exception:
                self.failed += 1
                if self.failed == 1 or self.failed % 100 == 0:
                    logger.warning(
                        'netbox_force: Graylog delivery failed (%d total)',
                        self.failed, exc_info=True)
            finally:
                try:
                    self._queue.task_done()
                except Exception:
                    pass

    # -- transports ------------------------------------------------------

    def _deliver(self, config, payload):
        transport = config['transport']
        data = _serialise(payload)
        if transport == 'udp':
            self._send_udp(config, data)
        elif transport in ('tcp', 'tcp-tls'):
            self._send_tcp(config, data)
        else:
            self._send_http(config, data)

    def _send_udp(self, config, data):
        # Resolved rather than hardcoded to AF_INET so an IPv6-only Graylog
        # host works without a separate setting.
        info = socket.getaddrinfo(config['host'], config['port'],
                                  socket.AF_UNSPEC, socket.SOCK_DGRAM)
        family, socktype, proto, _, address = info[0]
        sock = socket.socket(family, socktype, proto)
        try:
            sock.settimeout(config['timeout'])
            for chunk in _udp_chunks(data):
                sock.sendto(chunk, address)
        finally:
            sock.close()

    def _send_tcp(self, config, data):
        """
        GELF over TCP is null-byte delimited and must not be compressed. The
        connection is kept open; after a failure reconnection is deferred so a
        dead Graylog does not cost a full connect timeout per event.
        """
        key = (config['host'], config['port'], config['transport'],
               config['verify_ssl'])
        if self._tcp_config != key:
            self._close_tcp()
            self._tcp_config = key

        if self._tcp_socket is None:
            if time.time() < self._next_retry:
                raise GraylogError('backoff')
            self._tcp_socket = self._open_tcp(config)

        try:
            self._tcp_socket.sendall(data + b'\x00')
        except Exception:
            self._close_tcp()
            self._next_retry = time.time() + _TCP_RECONNECT_BACKOFF
            raise

    def _open_tcp(self, config):
        sock = socket.create_connection(
            (config['host'], config['port']), timeout=config['timeout'])
        if config['transport'] == 'tcp-tls':
            context = ssl.create_default_context()
            if not config['verify_ssl']:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=config['host'])
        sock.settimeout(config['timeout'])
        return sock

    def _close_tcp(self):
        if self._tcp_socket is not None:
            try:
                self._tcp_socket.close()
            except Exception:
                pass
        self._tcp_socket = None

    def _send_http(self, config, data):
        scheme = 'https' if config['transport'] == 'https' else 'http'
        url = f"{scheme}://{config['host']}:{config['port']}/gelf"
        request = Request(url, data=data, method='POST',
                          headers={'Content-Type': 'application/json'})
        context = None
        if scheme == 'https' and not config['verify_ssl']:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        response = urlopen(request, timeout=config['timeout'], context=context)
        response.close()


_sender = None
_sender_lock = threading.Lock()


def get_sender():
    global _sender
    if _sender is None:
        with _sender_lock:
            if _sender is None:
                _sender = GelfSender()
    return _sender


# =============================================================================
# CONFIGURATION
# =============================================================================

def build_config(settings_obj):
    """
    Extract the transport configuration from ForceSettings.

    Returns None when Graylog output is off or not configured, which every
    caller treats as "do nothing".
    """
    if settings_obj is None:
        return None
    if not getattr(settings_obj, 'graylog_enabled', False):
        return None
    host = (getattr(settings_obj, 'graylog_host', '') or '').strip()
    if not host:
        return None
    return {
        'host': host,
        'port': int(getattr(settings_obj, 'graylog_port', 12201) or 12201),
        'transport': getattr(settings_obj, 'graylog_transport', 'udp') or 'udp',
        'verify_ssl': bool(getattr(settings_obj, 'graylog_verify_ssl', True)),
        'timeout': int(getattr(settings_obj, 'graylog_timeout', 5) or 5),
        'source': (getattr(settings_obj, 'graylog_source_name', '') or '').strip()
                  or default_source_name(),
    }


def send_now(config, payload):
    """
    Deliver one payload synchronously. Only for the test button — never call
    this from a request path.

    UDP cannot confirm anything: a successful return means the datagram was
    handed to the kernel, not that Graylog received it. The UI says so.
    """
    from urllib.error import HTTPError

    sender = get_sender()
    try:
        sender._deliver(config, payload)
    except GraylogError:
        raise
    except HTTPError as exc:
        # A GELF HTTP input answers 202; anything else is a real answer from
        # Graylog and its status code says far more than "unreachable".
        raise GraylogError('network', f'HTTP {exc.code}')
    except socket.timeout as exc:
        raise GraylogError('timeout', str(exc))
    except socket.gaierror as exc:
        raise GraylogError('dns', str(exc))
    except ConnectionRefusedError as exc:
        raise GraylogError('refused', str(exc))
    except ssl.SSLError as exc:
        raise GraylogError('tls', str(exc))
    except OSError as exc:
        raise GraylogError('network', str(exc))
    except Exception as exc:
        raise GraylogError('internal', str(exc))
