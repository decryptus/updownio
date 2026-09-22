# updownio

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/updownio.svg)](https://pypi.org/project/updownio/)
[![PyPI version shields.io](https://img.shields.io/pypi/v/updownio.svg)](https://pypi.org/project/updownio/)
[![Documentation Status](https://readthedocs.org/projects/updownio/badge/?version=latest)](https://updownio.readthedocs.io/)

A Python client for the [updown.io REST API](https://updown.io/api).
Manage checks, retrieve downtime and performance data, configure alert recipients,
and maintain status pages from Python scripts.

Requires **Python 3.10 or newer**. It is a community client, not a monitoring
server. Only `requests` is required at runtime.

## Quick start

```sh
python -m pip install updownio
export UPDOWN_API_KEY='your-api-key'
```

```python
import updownio

checks = updownio.service('checks', timeout=15)
for check in checks.list():
    print(check['token'], check['url'], check['down'])
```

Use a read-only API key for reporting and a read/write key for changes. The API
key is sent in an HTTP header. Each `service()` call creates an independent
client: different accounts can safely coexist as separate client objects.

## Behaviour and errors

- Methods return decoded JSON (including valid empty lists and dictionaries).
- `delete()` returns the API's `deleted` value as a boolean; a missing URL returns `None`.
- URL selectors use exact matching and download the check list on every lookup.
  Use tokens for repeated operations. Duplicate URLs raise `ValueError`, so a
  write cannot silently select the wrong check. If both are supplied, token wins.
- `downtimes()` returns **one page**, not the full history. Use `params={'page': 2}`
  for subsequent pages (100 entries per page).
- Request data dictionaries are never modified by this library.
- Booleans use lowercase form values, lists use `name[]`, and dictionaries use
  `name[key]`. An empty list is sent as `name[]=`; omission leaves that field out.
  Empty dictionaries are rejected because form encoding is ambiguous. Individual
  empty header values remain supported. End-to-end array clearing on the hosted
  service has not been verified with an authenticated account.
- HTTP failures raise `updownio.UpDownIoError`, a subclass of `LookupError`, with
  `status_code`. Invalid JSON raises the same exception. HTTP 204 returns `None`.
  Error messages exclude request and response bodies to avoid exposing secrets.
- Network failures remain `requests.Timeout` / `requests.ConnectionError`.
  Requests are not retried automatically, to avoid repeating writes.
- Redirects are not followed, so the API-key header is not forwarded elsewhere.
- The timeout is a positive finite number of seconds, applied to connection and
  read inactivity separately; it is not an overall wall-clock deadline.
- `mk_api_call(raw_results=True)` returns the unvalidated Requests response;
  the caller must close it, including on errors.

```python
import requests
import updownio

client = updownio.service('checks')
try:
    checks = client.list()
except updownio.UpDownIoError as error:
    print('API failure:', error.status_code)
except requests.Timeout:
    print('Request timed out')
```

Configuration precedence: explicit argument, environment variable, default.
`UPDOWN_ENDPOINT` identifies the HTTP(S) origin; any path is replaced by
`/api/<service>`, preserving the historical behaviour. Use HTTPS for remote
services. Credentials, query strings and fragments in the endpoint are rejected.


## Installation

`pip install updownio`

## Environment variables

| Variable                 | Description                 | Default |
|:-------------------------|:----------------------------|:--------|
| `UPDOWN_ACCEPT`          | HTTP Accept request-header  | application/json |
| `UPDOWN_ACCEPT_ENCODING` | HTTP Accept-Encoding request-header | gzip |
| `UPDOWN_API_KEY`         | API key for authentication  | <span/> |
| `UPDOWN_ENDPOINT`        | API Endpoint                | https://updown.io |
| `UPDOWN_TIMEOUT`  | Request timeout in seconds  | 60 |

## Usage

### Import library

```python
import updownio
```

### Initialize service with arguments

```python
updown_checks = updownio.service('checks',
                                 api_key  = 'xxxxxxxxxxx',
                                 endpoint = 'https://updown.io',
                                 timeout  = 3600)
```

### Endpoints

#### Checks

##### List all your checks

```python
checks = updownio.service('checks').list()
```

##### Show a single check

Select check by token

```python
check = updownio.service('checks').show(token = 'xxxx')
```
or by URL

```python
check = updownio.service('checks').show(url = 'https://example.org')
```

##### Get all the downtimes of a check

Select downtimes by token

```python
check = updownio.service('checks').downtimes(token = 'xxxx',
                                             params = {'page': 1,
                                                       'results': False})
```
or by URL

```python
check = updownio.service('checks').downtimes(url = 'https://example.org')
```

##### Get detailed metrics about the check

Select metrics by token

```python
check = updownio.service('checks').metrics(token = 'xxxx',
                                           params = {'from': '2022-12-16 15:11:17 +0100',
                                                     'to': '2023-01-16 15:11:17 +0100',
                                                     'group': 'host'})
```
or by URL

```python
check = updownio.service('checks').metrics(url = 'https://example.org')
```

##### Add a new check

```python
check = updownio.service('checks').add('https://example.org',
                                       data = {'apdex_t': 2.0,
                                               'disabled_locations': ['fra', 'syd'],
                                               'period': 3600,
                                               'recipients': ['email:xxxxxxxx', 'slack:xxxxxxxx']})
```

##### Update a check

Select check by token

```python
check = updownio.service('checks').update(token = 'xxxx',
                                          data = {'apdex_t': 1.0,
                                                  'disabled_locations': ['fra', 'syd'],
                                                  'recipients': ['email:xxxxxxxx', 'slack:xxxxxxxx']})
```
or by URL

```python
check = updownio.service('checks').update(url = 'https://example.org',
                                          data = {'apdex_t': 1.0,
                                                  'disabled_locations': ['fra', 'syd'],
                                                  'recipients': ['email:xxxxxxxx', 'slack:xxxxxxxx']})
```

##### Delete a check

Select check by token

```python
updownio.service('checks').delete(token = 'xxxx')
```
or by URL

```python
updownio.service('checks').delete(url = 'https://example.org')
```

#### Nodes

##### List all updown.io monitoring nodes

```python
nodes = updownio.service('nodes').list()
```

##### List all updown.io monitoring nodes IPv4 addresses

```python
nodes = updownio.service('nodes').ipv4()
```

##### List all updown.io monitoring nodes IPv6 addresses

```python
nodes = updownio.service('nodes').ipv6()
```

#### Recipients

##### List all the possible alert recipients/channels on your account

```python
recipients = updownio.service('recipients').list()
```

##### Add a new recipient

```python
recipients = updownio.service('recipients').add(xtype = 'email',
                                                value = 'xxxxxxxx',
                                                data = {'selected': True})
```

##### Delete a recipient

```python
updownio.service('recipients').delete(xid = 'email:xxxxxxxx')
```

#### Status pages

##### List all your status pages

```python
status_pages = updownio.service('status_pages').list()
```

##### Add a new status page

```python
status_page = updownio.service('status_pages').add(['xxxx', 'yyyy', 'zzzz'],
                                                   data = {'name': 'foo',
                                                           'description': 'bar'})
```

##### Update a status page

```python
status_page = updownio.service('status_pages').update(token = 'xxxx',
                                                      data = {'checks': ['xxxx', 'zzzz'],
                                                              'name': 'spam',
                                                              'description': 'ham'})
```

##### Delete a status page

```python
updownio.service('status_pages').delete(token = 'xxxx')
```

## Additional endpoints

```python
all_node_ips = updownio.service('nodes').ips()
pulse = updownio.service('checks').add(data={'type': 'pulse', 'alias': 'backup'})
```

For options such as custom headers, HTTP methods and notification muting, pass
API fields through `data`. Consult the [API reference](https://updown.io/api) for
current values; this client does not duplicate the server's entire schema.

```python
updated = updownio.service('checks').update(
    token='xxxx',
    data={'custom_headers': {'X-Example': 'value'}, 'enabled': False},
)
```

## Upgrading from 0.0.7

Public service names and existing method arguments remain supported. Changes:

- Python 2 and Python 3.9 or older are no longer supported.
- Clients no longer share configuration. Code relying on singleton instances must
  keep and pass its client explicitly.
- Invalid data types raise an error rather than silently becoming empty data.
- Duplicate URL matches raise an error; use the desired check token.
- Empty responses are accepted; malformed JSON and HTTP errors are distinguished
  from connection failures. API error messages no longer contain server bodies.
- Internal registry entries are constructors rather than shared instances;
  registration still accepts either a service class or a legacy instance.
- `sonicprobe` is no longer a dependency; standard-library URL utilities suffice.

## Development

```sh
python -m pip install -e . build twine -r docs/requirements.txt
python -m unittest discover -s tests -v
python -m build
python -m twine check --strict dist/*
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Tests use simulated responses and a loopback HTTP server. They never create or
delete real updown.io resources. CI tests Python 3.10–3.14, builds distributions
and documentation, then installs the wheel outside the source directory.

## Releases

After successful tests on `main`, a new version in `VERSION`, `RELEASE` and
`setup.yml` creates `vX.Y.Z` and publishes that exact revision to PyPI via
Trusted Publishing. Existing versions are not overwritten. The workflow also
supports pushed version tags and a manual retry for an existing tag.
See [release configuration](docs/releases.md).
