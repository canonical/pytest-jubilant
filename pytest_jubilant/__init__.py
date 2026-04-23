#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest-jubilant provides pytest fixtures, options, and markers for use with Jubilant.

Jubilant is a Pythonic wrapper around the Juju CLI.
"""

from pytest_jubilant._main import JujuFactory

__all__ = ["JujuFactory"]
