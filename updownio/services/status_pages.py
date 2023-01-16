# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.status_pages"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES


_DEFAULT_API_PATH = "api/status_pages"

LOG               = logging.getLogger('updownio.status_pages')


class UpDownIoStatusPages(UpDownIoServiceBase):
    SERVICE_NAME = 'status_pages'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    @staticmethod
    def _build_checks(checks):
        r = []

        if not isinstance(checks, (list, tuple)):
            return r

        for x in enumerate(checks):
            if isinstance(x, str) and x.isalnum():
                r.append(('checks[]', checks))

        return r

    def list(self):
        return self.mk_api_call()

    def add(self, checks, data = None):
        if isinstance(checks, str):
            checks = [checks]

        if not isinstance(data, dict):
            data = {}

        data.pop('checks', None)

        data = list(data.items())
        data.extend(self._build_checks(checks))

        return self.mk_api_call(method = 'POST', data = data)

    def update(self, token, data = None):
        if not isinstance(data, dict):
            data = {}

        checks = data.pop('checks', None)
        data   = list(data.items())

        if checks:
            data.extend(self._build_checks(checks))

        return self.mk_api_call("%s" % token,
                                method = 'PUT',
                                data = data)

    def delete(self, token):
        r = self.mk_api_call("%s" % token,
                             method = 'DELETE')
        if not r:
            return False

        return bool(r.get('deleted'))


if __name__ != "__main__":
    def _start():
        SERVICES.register(UpDownIoStatusPages())
    _start()
