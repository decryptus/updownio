# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.checks"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES, copy_data, form_data, string_array, identifier


_DEFAULT_API_PATH = "api/checks"

LOG               = logging.getLogger('updownio.checks')


class UpDownIoChecks(UpDownIoServiceBase):
    SERVICE_NAME = 'checks'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    @staticmethod
    def _build_disabled_locations(values):
        return string_array("disabled_locations", values)

    @staticmethod
    def _build_recipients(values):
        return string_array("recipients", values)

    def _match_by_url(self, url):
        xlist = self.list()
        if not xlist:
            return None

        matches = [x for x in xlist if x.get('url') == url]
        if len(matches) > 1:
            raise ValueError("multiple checks match this URL; use a token")
        return matches[0] if matches else None

    def _fetch_token_from_url(self, url):
        x = self._match_by_url(url)
        if x:
            return x['token']

        return None

    def list(self):
        return self.mk_api_call()

    def show(self, token = None, url = None, params = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if token:
            return self.mk_api_call(identifier(token), params = params)

        match = self._match_by_url(url)
        if match is not None and params:
            return self.mk_api_call(identifier(match['token']), params=params)
        return match

    def downtimes(self, token = None, url = None, params = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        return self.mk_api_call("%s/downtimes" % identifier(token),
                                params = params)

    def metrics(self, token = None, url = None, params = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        return self.mk_api_call("%s/metrics" % identifier(token),
                                params = params)

    def add(self, url=None, data=None):
        data = copy_data(data)
        if url is not None:
            data['url'] = url
        if not data.get('url') and data.get('type') != 'pulse':
            raise ValueError("url is required except for pulse checks")
        return self.mk_api_call(method='POST', data=form_data(data))

    def update(self, token=None, url=None, data=None):
        data = copy_data(data)
        if not token and not url:
            raise ValueError("missing arguments token and url")
        if not token:
            token = self._fetch_token_from_url(url)
            if not token:
                return None
        return self.mk_api_call(identifier(token), method='PUT', data=form_data(data))

    def delete(self, token = None, url = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        r = self.mk_api_call(identifier(token),
                             method = 'DELETE')
        if not r:
            return False

        return bool(r.get('deleted'))


SERVICES.register(UpDownIoChecks)
