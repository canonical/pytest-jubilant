#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest-jubilant provides pytest-specific functionality on top of Jubilant.

Jubilant is a Pythonic wrapper around the Juju CLI.
"""

from pytest_jubilant._main import JujuFactory

__all__ = ["JujuFactory"]
