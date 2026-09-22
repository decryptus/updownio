# SPDX-License-Identifier: GPL-3.0-or-later
"""Python client for updown.io."""
from updownio.service import SERVICES, UpDownIoError
from updownio.services import checks, nodes, recipients, status_pages

__all__ = ["service", "UpDownIoError"]


def service(name, **kwargs):
    """Create an independent client for a named service."""
    if name not in SERVICES:
        raise ValueError("invalid service: %r" % name)
    return SERVICES[name]().init(**kwargs)
