"""
CheckMK REST API client.

Reads monitoring state only. The configuration (Setup/WATO) API is never
touched, so a read-only automation user holding just the 'guest' role is
sufficient — verified against CheckMK 2.3.0p48 Raw Edition, where
host_config returns an empty collection for such a user.

Release differences are handled by probing: the service collection is
requested in several forms until one succeeds, and the working form is
remembered in ForceSettings.checkmk_api_flavor. That keeps the plugin
working across CheckMK versions without a code change per release.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

# Raw CheckMK service states mapped to PatchVM.patch_status.
# UNKNOWN counts as a warning: the check is broken or the agent is silent,
# which needs attention but is not a confirmed critical finding.
STATE_MAP = {
    0: 'green',
    1: 'yellow',
    2: 'red',
    3: 'yellow',
}

STATE_LABELS = {0: 'OK', 1: 'WARN', 2: 'CRIT', 3: 'UNKNOWN'}

DEFAULT_SERVICE_PATTERN = 'Updates?'
DEFAULT_TIMEOUT = 10

_COLUMNS = ('host_name', 'description', 'state', 'plugin_output', 'last_check')

# Probe order for the service collection. Server-side filtering is preferred
# because it keeps a few thousand irrelevant services off the wire.
FLAVORS = (
    'query_ci',   # server-side regex filter, case-insensitive (~~)
    'query_cs',   # server-side regex filter, case-sensitive (~)
    'columns',    # explicit columns, filtered in Python
    'bare',       # no parameters at all, filtered in Python
)


class CheckmkError(Exception):
    """
    A failed CheckMK call, carrying a machine-readable code so the UI can
    show a translated explanation instead of an HTTP status number.
    """

    def __init__(self, code, detail=''):
        self.code = code
        self.detail = detail
        super().__init__(f'{code}: {detail}' if detail else code)


def normalize_base_url(url):
    """
    Reduce whatever the user pasted to 'scheme://host/site'.

    Copying the URL out of a running CheckMK session yields something like
    'https://host/mysite/check_mk/index.py?start_url=...' — accepting that
    directly avoids a class of setup failures that look like auth problems.
    """
    from urllib.parse import urlsplit, urlunsplit

    raw = (url or '').strip()
    if not raw:
        raise CheckmkError('no_url')
    if '://' not in raw:
        raw = 'https://' + raw

    parts = urlsplit(raw)
    if parts.scheme not in ('http', 'https'):
        raise CheckmkError('bad_scheme', parts.scheme)
    if not parts.netloc:
        raise CheckmkError('bad_url', raw)

    path = parts.path
    for marker in ('/check_mk', '/cmk'):
        idx = path.find(marker)
        if idx != -1:
            path = path[:idx]
            break
    path = path.rstrip('/')

    if not path.strip('/'):
        raise CheckmkError('missing_site', raw)

    return urlunsplit((parts.scheme, parts.netloc, path, '', ''))


class CheckmkClient:

    def __init__(self, url, username, secret, verify_ssl=True,
                 timeout=DEFAULT_TIMEOUT, flavor='auto'):
        self.base_url = normalize_base_url(url)
        self.api_url = f'{self.base_url}/check_mk/api/1.0'
        self.username = (username or '').strip()
        self.secret = secret or ''
        self.verify_ssl = bool(verify_ssl)
        self.timeout = int(timeout) or DEFAULT_TIMEOUT
        self.flavor = flavor if flavor in FLAVORS else 'auto'
        self.detected_flavor = None

        if not self.username or not self.secret:
            raise CheckmkError('no_credentials')

    @property
    def site(self):
        return self.base_url.rsplit('/', 1)[-1]

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.username} {self.secret}',
            'Accept': 'application/json',
        }

    def _get(self, path, params=None):
        import requests

        if not self.verify_ssl:
            try:
                import urllib3
                urllib3.disable_warnings(
                    urllib3.exceptions.InsecureRequestWarning)
            except Exception:
                pass

        url = f'{self.api_url}{path}'
        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
                # A redirect here always means 'not authenticated' or 'wrong
                # URL'; following it would return an HTML login page and turn
                # a clear error into a confusing parse failure.
                allow_redirects=False,
            )
        except requests.exceptions.SSLError as exc:
            raise CheckmkError('tls', str(exc))
        except requests.exceptions.Timeout:
            raise CheckmkError('timeout', f'{self.timeout}s')
        except requests.exceptions.ConnectionError as exc:
            raise CheckmkError('unreachable', str(exc))
        except Exception as exc:
            raise CheckmkError('request_failed', str(exc))

        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            if 'login.py' in location:
                raise CheckmkError('redirect_login', location)
            raise CheckmkError('unexpected_redirect', location)

        if resp.status_code in (401, 403):
            raise CheckmkError('auth', f'HTTP {resp.status_code}')
        if resp.status_code == 404:
            raise CheckmkError('not_found', url)
        if resp.status_code >= 400:
            raise CheckmkError(
                'http_error',
                f'HTTP {resp.status_code}: {resp.text[:300]}',
            )

        try:
            return resp.json()
        except ValueError:
            raise CheckmkError('bad_response', resp.text[:300])

    def get_version(self):
        """Returns (version_string, edition). Cheapest way to verify access."""
        data = self._get('/version')
        versions = data.get('versions') or {}
        return versions.get('checkmk') or data.get('version') or '?', \
            data.get('edition') or '?'

    def _service_params(self, flavor, pattern):
        columns = list(_COLUMNS)
        if flavor == 'bare':
            return None
        if flavor == 'columns':
            return [('columns', c) for c in columns]

        op = '~~' if flavor == 'query_ci' else '~'
        query = json.dumps(
            {'op': op, 'left': 'description', 'right': pattern})
        params = [('query', query)]
        params.extend(('columns', c) for c in columns)
        return params

    def fetch_update_services(self, pattern=DEFAULT_SERVICE_PATTERN):
        """
        Return the update-related services as a list of normalized dicts:
        {host_name, description, state, plugin_output}.

        Probes the query forms in order and remembers the one that worked.
        """
        pattern = (pattern or DEFAULT_SERVICE_PATTERN).strip() \
            or DEFAULT_SERVICE_PATTERN
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise CheckmkError('bad_pattern', str(exc))

        candidates = (self.flavor,) if self.flavor != 'auto' else FLAVORS
        last_error = None

        for flavor in candidates:
            try:
                data = self._get(
                    '/domain-types/service/collections/all',
                    params=self._service_params(flavor, pattern),
                )
            except CheckmkError as exc:
                # Auth and connectivity problems are not going to be fixed by
                # a different query form — stop probing and report them.
                if exc.code in ('auth', 'unreachable', 'timeout', 'tls',
                                'redirect_login', 'not_found'):
                    raise
                last_error = exc
                logger.debug('CheckMK flavor %s failed: %s', flavor, exc)
                continue

            rows = self._parse_services(data)
            # Server-side filtering already narrowed the set; the client-side
            # variants still have to apply the pattern themselves.
            if flavor in ('columns', 'bare'):
                rows = [r for r in rows if regex.search(r['description'])]

            self.detected_flavor = flavor
            return rows

        raise last_error or CheckmkError('no_flavor')

    def fetch_hosts(self):
        """
        Return {host_name: {'address', 'alias', 'state'}} from the monitoring
        API.

        Deliberately not host_config: that is the Setup/WATO API, which a
        read-only 'guest' automation user cannot see — it answers with an
        empty collection rather than an error. The Livestatus 'address'
        column carries the same IP and is readable.
        """
        columns = ('name', 'address', 'alias', 'state')
        attempts = (
            [('columns', c) for c in columns],
            None,  # some releases reject explicit columns; take the defaults
        )

        data = None
        last_error = None
        for params in attempts:
            try:
                data = self._get('/domain-types/host/collections/all', params=params)
                break
            except CheckmkError as exc:
                if exc.code in ('auth', 'unreachable', 'timeout', 'tls',
                                'redirect_login', 'not_found'):
                    raise
                last_error = exc
        if data is None:
            raise last_error or CheckmkError('bad_response', 'host collection')

        hosts = {}
        for item in (data.get('value') or []):
            if not isinstance(item, dict):
                continue
            ext = item.get('extensions')
            src = ext if isinstance(ext, dict) else item
            name = (src.get('name') or '').strip()
            if not name:
                continue
            try:
                state = int(src.get('state'))
            except (TypeError, ValueError):
                state = None
            hosts[name] = {
                'address': (src.get('address') or '').strip(),
                'alias': (src.get('alias') or '').strip(),
                'state': state,
            }
        return hosts

    @staticmethod
    def _parse_services(data):
        """
        Flatten the CheckMK collection response.

        Shape (2.3):
            {"value": [{"extensions": {"host_name": ..., "description": ...,
                                       "state": 2, "plugin_output": ...}}]}
        Older releases put the same keys directly on the item, so both are
        accepted.
        """
        if not isinstance(data, dict):
            raise CheckmkError('bad_response', 'response is not an object')

        rows = []
        for item in data.get('value') or []:
            if not isinstance(item, dict):
                continue
            ext = item.get('extensions')
            src = ext if isinstance(ext, dict) else item

            host = (src.get('host_name') or '').strip()
            desc = (src.get('description') or '').strip()
            if not host or not desc:
                continue

            try:
                state = int(src.get('state'))
            except (TypeError, ValueError):
                state = 3

            rows.append({
                'host_name': host,
                'description': desc,
                'state': state,
                'plugin_output': (src.get('plugin_output') or '').strip(),
            })

        return rows


def build_client(settings_obj):
    """Construct a client from ForceSettings, or raise CheckmkError."""
    if settings_obj is None:
        raise CheckmkError('no_settings')

    secret = settings_obj.get_checkmk_secret()
    return CheckmkClient(
        url=settings_obj.checkmk_url,
        username=settings_obj.checkmk_username,
        secret=secret,
        verify_ssl=settings_obj.checkmk_verify_ssl,
        timeout=settings_obj.checkmk_timeout,
        flavor=settings_obj.checkmk_api_flavor or 'auto',
    )
