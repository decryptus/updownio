# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.services.nodes"""


import logging

from updownio.service import UpDownIoServiceBase, SERVICES, copy_data, form_data, string_array, identifier


_DEFAULT_API_PATH = "api/nodes"

LOG               = logging.getLogger('updownio.nodes')


class UpDownIoNodes(UpDownIoServiceBase):
    SERVICE_NAME = 'nodes'

    @staticmethod
    def get_default_api_path():
        return _DEFAULT_API_PATH

    def list(self):
        return self.mk_api_call()

    def ips(self):
        return self.mk_api_call('/ips')

    def ipv4(self):
        return self.mk_api_call('/ipv4')

    def ipv6(self):
        return self.mk_api_call('/ipv6')


SERVICES.register(UpDownIoNodes)
