# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared HTTP transport and service registry."""

import abc
import math
import os
from email.utils import formatdate
from urllib.parse import quote, urlsplit, urlunsplit

import requests


class UpDownIoError(LookupError):
    """API failure; messages deliberately exclude request and response bodies."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class UpDownIoServices(dict):
    def register(self, service):
        # Accept legacy instance registration, but store constructors only.
        cls = service if isinstance(service, type) else type(service)
        if not issubclass(cls, UpDownIoServiceBase):
            raise TypeError("Invalid service class")
        self[cls.SERVICE_NAME] = cls


SERVICES = UpDownIoServices()


def copy_data(data):
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")
    return dict(data)


def string_array(name, values):
    if not isinstance(values, (list, tuple)) or any(
        not isinstance(value, str) or not value for value in values
    ):
        raise ValueError("%s must be a list or tuple of non-empty strings" % name)
    return [(name + "[]", value) for value in values] or [(name + "[]", "")]


def form_data(data):
    """Encode Rails-style arrays/hashes, retaining explicitly empty arrays."""
    result = []
    for key, value in data.items():
        if key in ("recipients", "disabled_locations", "checks") and value is not None:
            result.extend(string_array(key, value))
        elif key == "custom_headers" and value is not None and not isinstance(value, dict):
            raise ValueError("custom_headers must map strings to strings")
        elif isinstance(value, (list, tuple)):
            result.extend(string_array(key, value))
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                if not isinstance(subkey, str) or not isinstance(subvalue, str):
                    raise ValueError("%s must map strings to strings" % key)
                result.append(("%s[%s]" % (key, subkey), subvalue))
            if not value:
                raise ValueError("An empty mapping cannot be encoded unambiguously: %s" % key)
        elif value is not None:
            result.append((key, str(value).lower() if isinstance(value, bool) else value))
    return result


def identifier(value):
    if not isinstance(value, str) or not value or value in (".", ".."):
        raise ValueError("identifier must be a non-empty string")
    return quote(value, safe="")


def validated_timeout(value):
    if isinstance(value, bool):
        raise ValueError("timeout must be a positive finite number")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("timeout must be a positive finite number") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError("timeout must be a positive finite number")
    return value


class UpDownIoServiceBase(abc.ABC):
    SERVICE_NAME = None

    def __init__(self):
        self.api_key = None
        self.endpoint = None
        self.accept = None
        self.accept_encoding = None
        self.timeout = None

    @staticmethod
    @abc.abstractmethod
    def get_default_api_path():
        """Return the service path relative to the origin."""

    @staticmethod
    def get_default_accept():
        return "application/json"

    @staticmethod
    def get_default_accept_encoding():
        return "gzip"

    @staticmethod
    def get_default_endpoint():
        return "https://updown.io"

    @staticmethod
    def get_default_timeout():
        return 60

    @staticmethod
    def get_date():
        return formatdate(usegmt=True)

    def build_api_uri(self, path=None, query=None, fragment=None):
        uri = urlsplit(self.endpoint)
        return urlunsplit((uri.scheme, uri.netloc, path or "", query or "", fragment or ""))

    def mk_api_headers(self, date=None):
        return {"Accept": self.accept, "Accept-Encoding": self.accept_encoding,
                "Date": date or self.get_date(), "X-Api-Key": self.api_key}

    def mk_api_call(self, path="", method="GET", raw_results=False,
                    timeout=None, params=None, data=None):
        method = method.upper()
        if method not in ("GET", "POST", "PUT", "DELETE"):
            raise ValueError("unsupported HTTP method")
        suffix = "/" + path.strip("/") if path else ""
        uri = self.build_api_uri("/" + self.get_default_api_path() + suffix)
        timeout = self.timeout if timeout is None else validated_timeout(timeout)
        if isinstance(data, dict):
            data = form_data(data)
        if isinstance(params, dict):
            params = {k: str(v).lower() if isinstance(v, bool) else v for k, v in params.items()}
        # Do not forward the custom API-key header to redirect destinations.
        response = getattr(requests, method.lower())(
            uri, params=params, data=data, headers=self.mk_api_headers(),
            timeout=timeout, allow_redirects=False)
        if raw_results:
            return response  # The caller owns and closes the response.
        try:
            if not 200 <= response.status_code < 300:
                raise UpDownIoError("updown.io API returned HTTP %s" % response.status_code,
                                    response.status_code)
            if response.status_code == 204:
                return None
            try:
                return response.json()
            except ValueError:
                raise UpDownIoError("updown.io API returned invalid JSON", response.status_code) from None
        finally:
            response.close()

    def init(self, api_key=None, endpoint=None, timeout=None, accept=None, accept_encoding=None):
        def setting(value, name, default=None):
            return value if value is not None else os.environ.get(name, default)
        api_key = setting(api_key, "UPDOWN_API_KEY")
        if not isinstance(api_key, str) or not api_key.strip() or "\n" in api_key or "\r" in api_key:
            raise ValueError("missing or invalid updown api_key")
        endpoint = setting(endpoint, "UPDOWN_ENDPOINT", self.get_default_endpoint())
        uri = urlsplit(endpoint)
        if uri.scheme not in ("http", "https") or not uri.hostname or uri.username or uri.password or uri.query or uri.fragment:
            raise ValueError("endpoint must be an HTTP(S) URL without credentials, query or fragment")
        # Legacy endpoint paths are replaced by /api/<service>.
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = validated_timeout(setting(timeout, "UPDOWN_TIMEOUT", self.get_default_timeout()))
        self.accept = setting(accept, "UPDOWN_ACCEPT", self.get_default_accept())
        self.accept_encoding = setting(accept_encoding, "UPDOWN_ACCEPT_ENCODING", self.get_default_accept_encoding())
        return self
