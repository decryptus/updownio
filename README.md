## updownio project

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/updownio.svg)](https://pypi.org/project/updownio/)
[![PyPI version shields.io](https://img.shields.io/pypi/v/updownio.svg)](https://pypi.org/project/updownio/)
[![Documentation Status](https://readthedocs.org/projects/updownio/badge/?version=latest)](https://updownio.readthedocs.io/)

updownio is a free and open-source, it's a python wrapper for the updown.io API.

## Installation

`pip install updownio`

## Environment variables

| Variable                 | Description                 | Default |
|:-------------------------|:----------------------------|:--------|
| `UPDOWN_ACCEPT`          | HTTP Accept request-header  | application/json |
| `UPDOWN_ACCEPT_ENCODING` | HTTP Accept-Encoding request-header | gzip |
| `UPDOWN_API_KEY`         | API key for authentication  | <span/> |
| `UPDOWN_ENDPOINT`        | API Endpoint                | https://updown.io |
| `UPDOWN_TIMEOUT       `  | Request timeout in seconds  | 60 |

## Usage

### Import library

```python
import updownio
```

### Initialize service with arguments

```python
updown_checks = updownio.service('checks',
                                 api_key  = 'xxxxxxxxxxx',
                                 endpoint = 'https://example.org/api',
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
check = updownio.service('checks').downtimes(token = 'xxxx'
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

##### Update a new check

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

##### Update a new status page

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
