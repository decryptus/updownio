# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.checks"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES


_DEFAULT_API_PATH = "api/checks"

LOG               = logging.getLogger('updownio.checks')


class UpDownIoChecks(UpDownIoServiceBase):
    SERVICE_NAME = 'checks'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    @staticmethod
    def _build_disabled_locations(disabled_locations):
        r = []

        if not isinstance(disabled_locations, (list, tuple)):
            return r

        for x in enumerate(disabled_locations):
            if isinstance(x, str):
                r.append(('disabled_locations[]', x))

        return r

    @staticmethod
    def _build_recipients(recipients):
        r = []

        if not isinstance(recipients, (list, tuple)):
            return r

        for x in enumerate(recipients):
            if isinstance(x, str):
                r.append(('recipients[]', x))

        return r

    def _match_by_url(self, url):
        xlist = self.list()
        if not xlist:
            return None

        for x in xlist:
            if x['url'] == url:
                return x

        return None

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
            return self.mk_api_call(token, params = params)

        return self._match_by_url(url)

    def downtimes(self, token = None, url = None, params = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        return self.mk_api_call("%s/downtimes" % token,
                                params = params)

    def metrics(self, token = None, url = None, params = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        return self.mk_api_call("%s/metrics" % token,
                                params = params)

    def add(self, url, data = None):
        if not isinstance(data, dict):
            data = {}

        data['url']        = url
        disabled_locations = data.pop('disabled_locations', None)
        recipients         = data.pop('recipients', None)
        data               = list(data.items())

        if disabled_locations:
            data.extend(self._build_disabled_locations(disabled_locations))

        if recipients:
            data.extend(self._build_recipients(recipients))

        return self.mk_api_call(method = 'POST', data = data)

    def update(self, token = None, url = None, data = None):
        if not isinstance(data, dict):
            data = {}

        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        disabled_locations = data.pop('disabled_locations', None)
        recipients         = data.pop('recipients', None)
        data               = list(data.items())

        if disabled_locations:
            data.extend(self._build_disabled_locations(disabled_locations))

        if recipients:
            data.extend(self._build_recipients(recipients))

        return self.mk_api_call("%s" % token,
                                method = 'PUT',
                                data = data)

    def delete(self, token = None, url = None):
        if not token and not url:
            raise ValueError("missing arguments token and url")

        if not token and url:
            token = self._fetch_token_from_url(url)
            if not token:
                return None

        r = self.mk_api_call("%s" % token,
                             method = 'DELETE')
        if not r:
            return False

        return bool(r.get('deleted'))


if __name__ != "__main__":
    def _start():
        SERVICES.register(UpDownIoChecks())
    _start()
