# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.recipients"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES, copy_data, form_data, string_array, identifier


_DEFAULT_API_PATH = "api/recipients"

LOG               = logging.getLogger('updownio.recipients')


class UpDownIoRecipients(UpDownIoServiceBase):
    SERVICE_NAME = 'recipients'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    def list(self):
        return self.mk_api_call()

    def add(self, xtype, value, data = None):
        data = copy_data(data)

        data['type']  = xtype
        data['value'] = value

        return self.mk_api_call(method = 'POST', data = data)

    def delete(self, xid):
        r = self.mk_api_call(identifier(xid),
                             method = 'DELETE')
        if not r:
            return False

        return bool(r.get('deleted'))


SERVICES.register(UpDownIoRecipients)
