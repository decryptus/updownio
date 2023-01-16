# -*- coding: utf-8 -*-
# Copyright (C) 2023 Adrien Delle Cave
# SPDX-License-Identifier: GPL-3.0-or-later
"""updownio"""


import logging

from updownio.services import *
from updownio.service import SERVICES


def service(name, **kwargs):
    if name not in SERVICES:
        raise ValueError("invalid service: %r" % name)

    return SERVICES[name].init(**kwargs)
