"""
Graylog REST API client — reading only.

Scope of "read only", stated precisely because it matters:

* Every call this module makes either retrieves data or asks Graylog to run a
  search. Nothing creates, edits or deletes a stream, index, input, dashboard,
  user or message.
* The legacy search endpoint is a plain GET. The newer Views search API is not:
  it requires POSTing a search definition and then POSTing to execute it. That
  POST creates a short-lived search object inside Graylog and returns results;
  it does not alter stored data. If that is unacceptable in a given
  environment, pin the search form to `legacy` in the settings.
* The real guarantee is the token. Issue it for a Graylog user with a
  read-only role, and this plugin cannot do anything else regardless of what
  its code asks for.

Graylog releases differ in which search API exists, so the working form is
probed once and remembered in ForceSettings.graylog_search_flavor — the same
approach the CheckMK client uses.
"""

import logging

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
DEFAULT_PORT = 9000

# Search API forms, probed in this order.
#   legacy — GET /api/search/universal/relative, present up to Graylog 5.x
#   views  — POST /api/views/search, the replacement
SEARCH_FLAVORS = ('legacy', 'views')

# Syslog severities counted as errors and warnings for the per-source summary.
ERROR_LEVELS = (0, 1, 2, 3)
WARNING_LEVELS = (4,)


class GraylogApiError(Exception):
    """
    A failed Graylog call, carrying a machine-readable code so the UI can show
    a translated explanation instead of an HTTP status number.
    """

    def __init__(self, code, detail=''):
        self.code = code
        self.detail = detail
        super().__init__(f'{code}: {detail}' if detail else code)


def normalize_api_url(url):
    """
    Reduce whatever was pasted to 'scheme://host[:port]'.

    Copying the address out of a running Graylog session yields something like
    'https://graylog.example.com/search?q=...&rangetype=relative'. Accepting
    that directly avoids a class of setup failures that look like auth
    problems.
    """
    from urllib.parse import urlsplit, urlunsplit

    raw = (url or '').strip()
    if not raw:
        raise GraylogApiError('no_url')
    if '://' not in raw:
        raw = 'http://' + raw

    parts = urlsplit(raw)
    if parts.scheme not in ('http', 'https'):
        raise GraylogApiError('bad_scheme', parts.scheme)
    if not parts.netloc:
        raise GraylogApiError('bad_url', raw)

    # Graylog is commonly served under a path prefix behind a reverse proxy,
    # so the path is kept — but the UI routes below /api are not part of it.
    path = parts.path.rstrip('/')
    for marker in ('/api', '/search', '/streams', '/messages', '/dashboards'):
        idx = path.find(marker)
        if idx != -1:
            path = path[:idx]
            break
    path = path.rstrip('/')

    return urlunsplit((parts.scheme, parts.netloc, path, '', ''))


class GraylogClient:

    def __init__(self, url, token, verify_ssl=True, timeout=DEFAULT_TIMEOUT,
                 stream_id='', search_flavor='auto'):
        self.base_url = normalize_api_url(url)
        self.api_url = f'{self.base_url}/api'
        self.token = (token or '').strip()
        self.verify_ssl = bool(verify_ssl)
        self.timeout = int(timeout) or DEFAULT_TIMEOUT
        self.stream_id = (stream_id or '').strip()
        self.search_flavor = (search_flavor
                              if search_flavor in SEARCH_FLAVORS else 'auto')
        self.detected_flavor = None

        if not self.token:
            raise GraylogApiError('no_token')

    # -- plumbing --------------------------------------------------------

    def _auth(self):
        # Graylog authenticates an access token as the username with the
        # literal password "token".
        return (self.token, 'token')

    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            # Required by Graylog on any non-GET request as CSRF protection.
            'X-Requested-By': 'netbox-force',
        }

    def _request(self, method, path, params=None, body=None):
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
            resp = requests.request(
                method,
                url,
                auth=self._auth(),
                headers=self._headers(),
                params=params,
                json=body,
                timeout=self.timeout,
                verify=self.verify_ssl,
                # A redirect here always means 'not authenticated' or 'wrong
                # URL'; following it would return an HTML login page and turn
                # a clear error into a confusing parse failure.
                allow_redirects=False,
            )
        except requests.exceptions.SSLError as exc:
            raise GraylogApiError('tls', str(exc))
        except requests.exceptions.Timeout:
            raise GraylogApiError('timeout', f'{self.timeout}s')
        except requests.exceptions.ConnectionError as exc:
            raise GraylogApiError('unreachable', str(exc))
        except Exception as exc:
            raise GraylogApiError('request_failed', str(exc))

        if resp.status_code in (301, 302, 303, 307, 308):
            raise GraylogApiError('unexpected_redirect',
                                  resp.headers.get('Location', ''))
        if resp.status_code in (401, 403):
            raise GraylogApiError('auth', f'HTTP {resp.status_code}')
        if resp.status_code == 404:
            raise GraylogApiError('not_found', path)
        if resp.status_code >= 400:
            raise GraylogApiError(
                'http_error', f'HTTP {resp.status_code}: {resp.text[:300]}')

        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            raise GraylogApiError('bad_response', resp.text[:300])

    def _get(self, path, params=None):
        return self._request('GET', path, params=params)

    # -- system ----------------------------------------------------------

    def get_version(self):
        """Returns (version, node_id, cluster_id). Cheapest access check."""
        data = self._get('/system')
        return (data.get('version') or '?',
                data.get('node_id') or '',
                data.get('cluster_id') or '')

    def cluster_nodes(self):
        """
        One dict per Graylog node: id, hostname, is_leader, transport_address.

        Needs a token whose role may read cluster information. When it may not,
        the caller turns the resulting 'auth' error into "no permission" rather
        than into a blank panel.
        """
        data = self._get('/system/cluster/nodes')
        nodes = []
        for item in (data.get('nodes') or []):
            if not isinstance(item, dict):
                continue
            nodes.append({
                'id': item.get('node_id') or '',
                'hostname': (item.get('hostname') or '').strip(),
                'transport_address': item.get('transport_address') or '',
                'is_leader': bool(item.get('is_leader')
                                  or item.get('is_master')),
                'type': item.get('type') or '',
            })
        return nodes

    def node_status(self, node_id):
        """
        Per-node liveness and journal backlog.

        The journal is the useful early warning: a backlog that keeps growing
        means Graylog is accepting faster than it can index, and messages will
        eventually be dropped.
        """
        result = {'alive': False, 'lb_status': '', 'journal_entries': None,
                  'journal_size': None}
        try:
            info = self._get(f'/cluster/{node_id}')
            result['alive'] = bool(info.get('is_processing', True))
            result['lifecycle'] = info.get('lifecycle') or ''
            result['lb_status'] = info.get('lb_status') or ''
        except GraylogApiError:
            return result
        try:
            journal = self._get(f'/cluster/{node_id}/journal')
            result['journal_entries'] = journal.get('uncommitted_journal_entries')
            result['journal_size'] = journal.get('journal_size')
            result['append_rate'] = journal.get('append_events_per_second')
            result['read_rate'] = journal.get('read_events_per_second')
        except GraylogApiError:
            pass
        return result

    def indexer_health(self):
        """
        Elasticsearch/OpenSearch cluster health — literally green, yellow or
        red, which is exactly the traffic light the UI wants.
        """
        data = self._get('/system/indexer/cluster/health')
        return {
            'status': (data.get('status') or '').lower(),
            'shards': data.get('shards') or {},
        }

    def streams(self):
        """[(id, title)] for the stream picker."""
        data = self._get('/streams')
        out = []
        for item in (data.get('streams') or []):
            if isinstance(item, dict) and item.get('id'):
                out.append((item['id'], item.get('title') or item['id']))
        return sorted(out, key=lambda pair: pair[1].lower())

    # -- search ----------------------------------------------------------

    def _flavor_candidates(self):
        return (self.search_flavor,) if self.search_flavor != 'auto' \
            else SEARCH_FLAVORS

    @staticmethod
    def _fatal(code):
        """Errors that a different search form will not fix."""
        return code in ('auth', 'unreachable', 'timeout', 'tls',
                        'unexpected_redirect', 'no_token')

    def count_by_source(self, range_seconds, query='*', limit=1000):
        """
        Message counts grouped by source, for the whole installation, in one
        call.

        This is the reason the polling job is cheap: it does not ask Graylog
        once per NetBox device. It asks once and joins locally.

        Returns {source: {'total': int, 'errors': int, 'warnings': int}}.
        """
        totals = self._terms('source', query, range_seconds, limit)
        errors = self._terms(
            'source', self._and(query, self._level_filter(ERROR_LEVELS)),
            range_seconds, limit)
        warnings = self._terms(
            'source', self._and(query, self._level_filter(WARNING_LEVELS)),
            range_seconds, limit)

        out = {}
        for name, count in totals.items():
            out[name] = {
                'total': count,
                'errors': errors.get(name, 0),
                'warnings': warnings.get(name, 0),
            }
        return out

    @staticmethod
    def _and(left, right):
        if not right:
            return left
        if not left or left.strip() == '*':
            return right
        return f'({left}) AND ({right})'

    @staticmethod
    def _level_filter(levels):
        return ' OR '.join(f'level:{value}' for value in levels)

    def _terms(self, field, query, range_seconds, limit):
        last_error = None
        for flavor in self._flavor_candidates():
            try:
                if flavor == 'legacy':
                    result = self._terms_legacy(field, query, range_seconds, limit)
                else:
                    result = self._terms_views(field, query, range_seconds, limit)
            except GraylogApiError as exc:
                if self._fatal(exc.code):
                    raise
                last_error = exc
                logger.debug('Graylog search flavor %s failed: %s', flavor, exc)
                continue
            self.detected_flavor = flavor
            return result
        raise last_error or GraylogApiError('no_flavor')

    def _terms_legacy(self, field, query, range_seconds, limit):
        params = {
            'field': field,
            'query': query or '*',
            'range': int(range_seconds),
            'size': int(limit),
        }
        if self.stream_id:
            params['filter'] = f'streams:{self.stream_id}'
        data = self._get('/search/universal/relative/terms', params=params)
        terms = data.get('terms') or {}
        return {str(name): int(count) for name, count in terms.items()}

    def _terms_views(self, field, query, range_seconds, limit):
        """
        Aggregation through the Views search API.

        Two POSTs: one to register the search, one to execute it. Neither
        stores anything durable — see the module docstring.
        """
        search = {
            'queries': [{
                'id': 'q0',
                'query': {'type': 'elasticsearch', 'query_string': query or '*'},
                'timerange': {'type': 'relative', 'range': int(range_seconds)},
                'filter': ({'type': 'stream', 'id': self.stream_id}
                           if self.stream_id else None),
                'search_types': [{
                    'id': 'agg',
                    'type': 'pivot',
                    'rollup': True,
                    'row_groups': [{
                        'type': 'values',
                        'field': field,
                        'limit': int(limit),
                    }],
                    'series': [{'type': 'count', 'id': 'count()'}],
                }],
            }],
        }
        created = self._request('POST', '/views/search', body=search)
        search_id = created.get('id')
        if not search_id:
            raise GraylogApiError('bad_response', 'search id missing')

        result = self._request('POST', f'/views/search/{search_id}/execute',
                               body={})
        return self._parse_pivot(result)

    @staticmethod
    def _parse_pivot(result):
        """
        Flatten the Views pivot response into {value: count}.

        Shape:
          results.q0.search_types.agg.rows[] with
          {key: ['srv-01'], values: [{value: 42, source: 'row-leaf'}]}
        The total row carries an empty key and is skipped.
        """
        out = {}
        try:
            queries = (result.get('results') or {}).values()
        except AttributeError:
            return out

        for query_result in queries:
            search_types = (query_result or {}).get('search_types') or {}
            for payload in search_types.values():
                for row in (payload or {}).get('rows') or []:
                    key = row.get('key') or []
                    if not key:
                        continue
                    count = 0
                    for value in row.get('values') or []:
                        if value.get('source') in ('row-leaf', 'leaf'):
                            try:
                                count = int(value.get('value') or 0)
                            except (TypeError, ValueError):
                                count = 0
                            break
                    out[str(key[0])] = count
        return out

    def messages_for_source(self, source, range_seconds, limit=25,
                            extra_query=''):
        """
        Recent messages for one host, newest first.

        Used by the panel on the device and VM pages. Deliberately small and
        deliberately not a search interface — for anything beyond a glance the
        page links into Graylog itself.
        """
        # Quotes are stripped rather than escaped: a source name containing one
        # is not worth supporting, and leaving it in would let the value break
        # out of the quoted term and rewrite the query.
        source_query = 'source:"{}"'.format(str(source).replace('"', ''))
        query = self._and(source_query, extra_query)

        last_error = None
        for flavor in self._flavor_candidates():
            try:
                if flavor == 'legacy':
                    rows = self._messages_legacy(query, range_seconds, limit)
                else:
                    rows = self._messages_views(query, range_seconds, limit)
            except GraylogApiError as exc:
                if self._fatal(exc.code):
                    raise
                last_error = exc
                continue
            self.detected_flavor = flavor
            return rows
        raise last_error or GraylogApiError('no_flavor')

    def _messages_legacy(self, query, range_seconds, limit):
        params = {
            'query': query,
            'range': int(range_seconds),
            'limit': int(limit),
            'sort': 'timestamp:desc',
        }
        if self.stream_id:
            params['filter'] = f'streams:{self.stream_id}'
        data = self._get('/search/universal/relative', params=params)
        return [self._normalize_message((item or {}).get('message') or {})
                for item in (data.get('messages') or [])]

    def _messages_views(self, query, range_seconds, limit):
        search = {
            'queries': [{
                'id': 'q0',
                'query': {'type': 'elasticsearch', 'query_string': query},
                'timerange': {'type': 'relative', 'range': int(range_seconds)},
                'filter': ({'type': 'stream', 'id': self.stream_id}
                           if self.stream_id else None),
                'search_types': [{
                    'id': 'msgs',
                    'type': 'messages',
                    'limit': int(limit),
                    'offset': 0,
                    'sort': [{'field': 'timestamp', 'order': 'DESC'}],
                }],
            }],
        }
        created = self._request('POST', '/views/search', body=search)
        search_id = created.get('id')
        if not search_id:
            raise GraylogApiError('bad_response', 'search id missing')
        result = self._request('POST', f'/views/search/{search_id}/execute',
                               body={})

        rows = []
        for query_result in (result.get('results') or {}).values():
            for payload in ((query_result or {}).get('search_types') or {}).values():
                for entry in (payload or {}).get('messages') or []:
                    rows.append(self._normalize_message(
                        (entry or {}).get('message') or {}))
        return rows[:limit]

    @staticmethod
    def _normalize_message(message):
        try:
            level = int(message.get('level'))
        except (TypeError, ValueError):
            level = None
        return {
            'timestamp': message.get('timestamp') or '',
            'source': message.get('source') or '',
            'message': (message.get('message') or '')[:500],
            'level': level,
            'facility': message.get('facility') or '',
            'id': message.get('_id') or '',
            'index': message.get('_index') or '',
        }

    # -- deep links ------------------------------------------------------

    def search_url(self, query, range_seconds):
        """A link that opens this search in the Graylog UI."""
        from urllib.parse import urlencode

        params = {
            'q': query,
            'rangetype': 'relative',
            'relative': int(range_seconds),
        }
        if self.stream_id:
            return f'{self.base_url}/streams/{self.stream_id}/search?' \
                   + urlencode(params)
        return f'{self.base_url}/search?' + urlencode(params)


def build_client(settings_obj):
    """Construct a client from ForceSettings, or raise GraylogApiError."""
    if settings_obj is None:
        raise GraylogApiError('no_settings')

    return GraylogClient(
        url=settings_obj.graylog_api_url,
        token=settings_obj.get_graylog_token(),
        verify_ssl=settings_obj.graylog_api_verify_ssl,
        timeout=settings_obj.graylog_api_timeout,
        stream_id=settings_obj.graylog_stream_id,
        search_flavor=settings_obj.graylog_search_flavor or 'auto',
    )
