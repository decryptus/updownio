"""Offline regression tests; never contact a monitoring account."""
import ast
import copy
import json
import os
from pathlib import Path
import re
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch
from urllib.parse import parse_qs

import requests
import updownio
from updownio.service import UpDownIoServiceBase, UpDownIoServices


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = updownio.service('checks', api_key='dummy')

    def response(self, status=200, payload=None, text=None):
        response = requests.Response()
        response.status_code = status
        response._content = (text if text is not None else json.dumps(payload)).encode()
        response.close = Mock()
        return response

    def test_clients_are_independent(self):
        other = updownio.service('checks', api_key='other', timeout=7)
        self.assertIsNot(self.client, other)
        self.assertEqual(self.client.api_key, 'dummy')
        self.assertEqual(self.client.timeout, 60)
        self.assertEqual(other.timeout, 7)

    def test_factory_and_registry(self):
        with self.assertRaises(ValueError): updownio.service('unknown', api_key='dummy')
        with self.assertRaises(TypeError): UpDownIoServices().register(object())
        with self.assertRaises(TypeError): UpDownIoServiceBase()
        registry = UpDownIoServices()
        registry.register(self.client)
        self.assertIs(registry['checks'], type(self.client))

    def test_environment_and_precedence(self):
        with patch.dict(os.environ, {'UPDOWN_API_KEY':'env', 'UPDOWN_TIMEOUT':'2.5'}):
            client = updownio.service('nodes')
            self.assertEqual(client.timeout, 2.5)
            self.assertEqual(client.api_key, 'env')
            self.assertEqual(updownio.service('nodes', api_key='arg', timeout=3).timeout, 3)
        with self.assertRaises(ValueError): updownio.service('checks')

    def test_bad_timeouts(self):
        for timeout in [0, -1, True, 'bad', 'nan', float('inf')]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                updownio.service('checks', api_key='dummy', timeout=timeout)
        with self.assertRaises(ValueError): self.client.mk_api_call(timeout=0)

    def test_endpoint_and_identifier(self):
        for endpoint in ['file:///tmp/test', 'https://user:pass@example.org', 'https://example.org/?secret=x', 'https://example.org/#fragment']:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                updownio.service('checks', api_key='dummy', endpoint=endpoint)
        client = updownio.service('checks', api_key='dummy', endpoint='https://example.org/legacy')
        with patch('requests.get', return_value=self.response(payload={})) as call:
            client.show(token='a/b?c#d')
            self.assertEqual(call.call_args.args[0], 'https://example.org/api/checks/a%2Fb%3Fc%23d')
            self.assertFalse(call.call_args.kwargs['allow_redirects'])
        with self.assertRaises(ValueError): client.show(token='..')

    def test_valid_empty_json(self):
        for payload in [[], {}, False, 0, None]:
            response = self.response(payload=payload)
            with self.subTest(payload=payload), patch('requests.get', return_value=response):
                self.assertEqual(self.client.list(), payload)
                response.close.assert_called_once()

    def test_http_errors_are_closed_and_redacted(self):
        for status in [301, 401, 403, 404, 422, 429, 500]:
            response = self.response(status, text='secret response')
            with self.subTest(status=status), patch('requests.get', return_value=response):
                with self.assertRaises(updownio.UpDownIoError) as caught: self.client.list()
                self.assertIsInstance(caught.exception, LookupError)
                self.assertEqual(caught.exception.status_code, status)
                self.assertNotIn('secret', str(caught.exception))
                response.close.assert_called_once()

    def test_invalid_json_and_no_content(self):
        response = self.response(text='not json')
        with patch('requests.get', return_value=response), self.assertRaises(updownio.UpDownIoError): self.client.list()
        response.close.assert_called_once()
        with patch('requests.get', return_value=self.response(204, text='')): self.assertIsNone(self.client.list())

    def test_raw_response_ownership(self):
        response = self.response(500, text='error')
        with patch('requests.get', return_value=response):
            self.assertIs(self.client.mk_api_call(raw_results=True), response)
        response.close.assert_not_called()
        response.close()

    def test_network_errors_no_retry(self):
        for error in [requests.Timeout, requests.ConnectionError]:
            with patch('requests.post', side_effect=error('offline')) as call:
                with self.assertRaises(error): self.client.add('https://example.org')
                self.assertEqual(call.call_count, 1)

    def test_checks_form_preserves_inputs(self):
        data = {'disabled_locations':['fra','syd'], 'recipients':['email:123'],
                'custom_headers':{'X-Api-Key':'example'}, 'enabled':False, 'alias':'A & B'}
        original = copy.deepcopy(data)
        for method in ['add','update']:
            with self.subTest(method=method), patch('requests.' + ('post' if method == 'add' else 'put'), return_value=self.response(payload={})) as call:
                if method == 'add': self.client.add('https://example.org', data=data)
                else: self.client.update(token='abcd', data=data)
                body = requests.Request('POST', 'https://example.org', data=call.call_args.kwargs['data']).prepare().body
                parsed = parse_qs(body)
                self.assertEqual(parsed['disabled_locations[]'], ['fra','syd'])
                self.assertEqual(parsed['recipients[]'], ['email:123'])
                self.assertEqual(parsed['custom_headers[X-Api-Key]'], ['example'])
                self.assertEqual(parsed['enabled'], ['false'])
                self.assertEqual(parsed['alias'], ['A & B'])
                self.assertEqual(data, original)

    def test_empty_arrays_are_explicit(self):
        with patch('requests.put', return_value=self.response(payload={})) as call:
            self.client.update(token='abcd', data={'recipients':[], 'disabled_locations':[]})
            self.assertEqual(call.call_args.kwargs['data'], [('recipients[]',''), ('disabled_locations[]','')])

    def test_invalid_data(self):
        for data in ['wrong', []]:
            with self.assertRaises(TypeError): self.client.update(token='abcd', data=data)
        for data in [{'recipients':[3]}, {'custom_headers':{'X-Test':3}}, {'custom_headers':{}}]:
            with self.assertRaises(ValueError): self.client.update(token='abcd', data=data)
        with self.assertRaises(ValueError): self.client.add()

    def test_pulse_check(self):
        with patch('requests.post', return_value=self.response(payload={'token':'pulse'})) as call:
            self.assertEqual(self.client.add(data={'type':'pulse'})['token'], 'pulse')
            self.assertEqual(call.call_args.kwargs['data'], [('type','pulse')])

    def test_show_by_url_parameters(self):
        with patch('requests.get', side_effect=[self.response(payload=[{'url':'https://example.org','token':'abcd'}]), self.response(payload={'metrics':{}})]) as call:
            self.assertEqual(self.client.show(url='https://example.org',params={'metrics':True}), {'metrics':{}})
            self.assertEqual(call.call_count,2)
            self.assertTrue(call.call_args.args[0].endswith('/abcd'))
            self.assertEqual(call.call_args.kwargs['params'], {'metrics':'true'})

    def test_missing_and_ambiguous_url(self):
        for name in ['show','downtimes','metrics','update','delete']:
            with self.subTest(name=name), patch('requests.get',return_value=self.response(payload=[])):
                self.assertIsNone(getattr(self.client,name)(url='missing'))
            with self.assertRaises(ValueError): getattr(self.client,name)()
        with patch('requests.get',return_value=self.response(payload=[{'url':'same','token':'a'},{'url':'same','token':'b'}])):
            with self.assertRaisesRegex(ValueError,'multiple'): self.client.delete(url='same')

    def test_metrics_and_downtimes_routes(self):
        for name in ['metrics','downtimes']:
            with self.subTest(name=name), patch('requests.get',return_value=self.response(payload=[])) as call:
                getattr(self.client,name)(token='abcd',params={'page':2})
                self.assertTrue(call.call_args.args[0].endswith('/abcd/'+name))
                self.assertEqual(call.call_args.kwargs['params'],{'page':2})

    def test_all_service_list_routes(self):
        for name in ['checks','nodes','recipients','status_pages']:
            with self.subTest(name=name), patch('requests.get',return_value=self.response(payload=[])) as call:
                updownio.service(name,api_key='dummy').list()
                self.assertEqual(call.call_args.args[0],'https://updown.io/api/'+name)

    def test_nodes_routes(self):
        client=updownio.service('nodes',api_key='dummy')
        for name in ['ips','ipv4','ipv6']:
            with self.subTest(name=name), patch('requests.get',return_value=self.response(payload=[])) as call:
                getattr(client,name)()
                self.assertTrue(call.call_args.args[0].endswith('/nodes/'+name))

    def test_recipients(self):
        client=updownio.service('recipients',api_key='dummy')
        data={'selected':False}
        with patch('requests.post',return_value=self.response(201,payload={'id':'email:123'})) as call:
            client.add('email','a@example.org',data=data)
            self.assertEqual(dict(call.call_args.kwargs['data']),{'type':'email','value':'a@example.org','selected':'false'})
            self.assertEqual(data,{'selected':False})

    def test_status_pages(self):
        client=updownio.service('status_pages',api_key='dummy')
        with patch('requests.post',return_value=self.response(payload={})) as call:
            client.add(['abcd','efgh'],data={'name':'demo'})
            self.assertEqual(call.call_args.kwargs['data'],[('name','demo'),('checks[]','abcd'),('checks[]','efgh')])
        for checks in [[],['abcd'],'abcd']:
            data={'checks':checks,'name':'demo'}; original=copy.deepcopy(data)
            with patch('requests.put',return_value=self.response(payload={})) as call:
                client.update('page',data=data)
                self.assertEqual(data,original)
                self.assertIn(('checks[]','abcd' if checks else ''),call.call_args.kwargs['data'])

    def test_delete_services(self):
        for service,kwargs in [('checks',{'token':'abcd'}),('recipients',{'xid':'email:123'}),('status_pages',{'token':'page'})]:
            client=updownio.service(service,api_key='dummy')
            for deleted in [True,False]:
                with self.subTest(service=service,deleted=deleted), patch('requests.delete',return_value=self.response(payload={'deleted':deleted})):
                    self.assertEqual(client.delete(**kwargs),deleted)

    def test_readme_python_syntax(self):
        for block in re.findall(r'```python\n(.*?)```',Path('README.md').read_text(),re.S):
            ast.parse(block)


class WireTests(unittest.TestCase):
    def test_real_http_encoding_and_redirect(self):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                captured.append((self.path,self.headers.get('X-Api-Key'),parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode(),keep_blank_values=True)))
                self.send_response(201);self.end_headers();self.wfile.write(b'{"token":"abcd"}')
            def do_GET(self):
                captured.append(self.path)
                if self.path=='/api/checks':
                    self.send_response(302);self.send_header('Location','/other')
                else:self.send_response(200)
                self.end_headers();self.wfile.write(b'[]')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            client=updownio.service('checks',api_key='dummy',endpoint='http://127.0.0.1:%s'%server.server_port)
            self.assertEqual(client.add('https://example.org',data={'recipients':['email:1'],'enabled':False}),{'token':'abcd'})
            self.assertEqual(captured[0],('/api/checks','dummy',{'url':['https://example.org'],'recipients[]':['email:1'],'enabled':['false']}))
            with self.assertRaises(updownio.UpDownIoError):client.list()
            self.assertNotIn('/other',captured)
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
