#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Minimal test charm for pack and deploy."""

import logging

import ops

logger = logging.getLogger("simple-charm")
logger.setLevel(logging.DEBUG)


class SimpleCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        framework.observe(self.on["log"].action, self._on_log_action)

    def _on_log_action(self, event: ops.ActionEvent):
        for i in range(1, 10_000 + 1):
            logger.warning("Hello, it is I! '%s'", i)

    def _on_collect_status(self, event: ops.CollectStatusEvent):
        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(SimpleCharm)
