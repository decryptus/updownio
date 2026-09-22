# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.status_pages"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES, copy_data, form_data, string_array, identifier


_DEFAULT_API_PATH = "api/status_pages"

LOG               = logging.getLogger('updownio.status_pages')


class UpDownIoStatusPages(UpDownIoServiceBase):
    SERVICE_NAME = 'status_pages'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    @staticmethod
    def _build_checks(checks):
        if isinstance(checks, str):
            checks = [checks]
        return string_array("checks", checks)

    def list(self):
        return self.mk_api_call()

    def add(self, checks, data = None):
        if isinstance(checks, str):
            checks = [checks]

        data = copy_data(data)

        data.pop('checks', None)

        data = form_data(data)
        data.extend(self._build_checks(checks))

        return self.mk_api_call(method = 'POST', data = data)

    def update(self, token, data = None):
        data = copy_data(data)

        checks = data.pop('checks', None)
        data   = form_data(data)

        if checks is not None:
            data.extend(self._build_checks(checks))

        return self.mk_api_call(identifier(token),
                                method = 'PUT',
                                data = data)

    def delete(self, token):
        r = self.mk_api_call(identifier(token),
                             method = 'DELETE')
        if not r:
            return False

        return bool(r.get('deleted'))


SERVICES.register(UpDownIoStatusPages)
