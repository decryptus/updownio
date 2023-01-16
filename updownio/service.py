# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio.service"""


import abc
import os

from datetime import datetime

import logging
import requests

from sonicprobe.libs import urisup


LOG = logging.getLogger('updownio.service')


class UpDownIoServices(dict):
    def register(self, service):
        if not isinstance(service, UpDownIoServiceBase):
            raise TypeError("Invalid Service class. (class: %r)" % service)
        return dict.__setitem__(self, service.SERVICE_NAME, service)

SERVICES = UpDownIoServices()

_DEFAULT_ACCEPT          = "application/json"
_DEFAULT_ACCEPT_ENCODING = "gzip"
_DEFAULT_ENDPOINT        = "https://updown.io"
_DEFAULT_TIMEOUT         = 60

_DATE_FORMAT_GMT         = '%a, %d %b %Y %H:%M:%S GMT'


class UpDownIoServiceBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def SERVICE_NAME(self):
        return

    def __init__(self):
        self.api_key         = None
        self.endpoint        = None
        self.accept          = None
        self.accept_encoding = None
        self.timeout         = None

    @staticmethod
    @abc.abstractmethod
    def get_default_api_path():
        return

    @staticmethod
    def get_default_accept():
        return _DEFAULT_ACCEPT

    @staticmethod
    def get_default_accept_encoding():
        return _DEFAULT_ACCEPT_ENCODING

    @staticmethod
    def get_default_endpoint():
        return _DEFAULT_ENDPOINT

    @staticmethod
    def get_default_timeout():
        return _DEFAULT_TIMEOUT

    @staticmethod
    def get_date():
        return datetime.utcnow().strftime(_DATE_FORMAT_GMT)

    def build_api_uri(self, path = None, query = None, fragment = None):
        uri = list(urisup.uri_help_split(self.endpoint))
        uri[2:5] = (path, query, fragment)

        return urisup.uri_help_unsplit(uri)

    def mk_api_headers(self, date = None):
        if not date:
            date = self.get_date()

        return {'Accept': self.accept,
                'Accept-Encoding': self.accept_encoding,
                'Date': date,
                'X-Api-Key': self.api_key}

    def mk_api_call(self, path = "", method = 'GET', raw_results = False, timeout = None, params = None, data = None):
        if path:
            path = "/%s" % path.strip('/')
        else:
            path = ""

        r = None

        try:
            uri = self.build_api_uri("/%s%s" % (self.get_default_api_path(), path))

            r = getattr(requests, method.lower())(uri,
                                                  params  = params,
                                                  data    = data,
                                                  headers = self.mk_api_headers(),
                                                  timeout = timeout or self.timeout)

            if raw_results:
                return r

            if not r or r.status_code not in (200, 201) or not r.text:
                LOG.error("unable to call uri: %r. (params: %r, data: %r)", uri, params, data)
                raise LookupError("unable to call uri: %r. (response: %r)" % (uri, r.text))

            res = r.json()
            if not res:
                raise LookupError("invalid response for %r" % path)

            return res
        finally:
            if r:
                r.close()

    def init(self, api_key = None, endpoint = None, timeout = None, accept = None, accept_encoding = None):
        if api_key:
            self.api_key = api_key
        elif os.environ.get('UPDOWN_API_KEY'):
            self.api_key = os.environ['UPDOWN_API_KEY']
        else:
            raise ValueError("missing updownio api_key")

        if endpoint:
            self.endpoint = endpoint
        elif os.environ.get('UPDOWN_ENDPOINT'):
            self.endpoint = os.environ['UPDOWN_ENDPOINT']
        else:
            self.endpoint = self.get_default_endpoint()

        if accept:
            self.accept = accept
        elif os.environ.get('UPDOWN_ACCEPT'):
            self.accept = os.environ['UPDOWN_ACCEPT']
        else:
            self.accept = self.get_default_accept()

        if accept_encoding:
            self.accept_encoding = accept_encoding
        elif os.environ.get('UPDOWN_ACCEPT_ENCODING'):
            self.accept_encoding = os.environ['UPDOWN_ACCEPT_ENCODING']
        else:
            self.accept_encoding = self.get_default_accept_encoding()

        if timeout:
            self.timeout = timeout
        elif os.environ.get('UPDOWN_TIMEOUT'):
            self.timeout = os.environ['UPDOWN_TIMEOUT']
        else:
            self.timeout = self.get_default_timeout()

        return self
