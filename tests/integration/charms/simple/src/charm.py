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
        framework.observe(self.on["exec"].action, self._on_exec_action)

    def _on_exec_action(self, event: ops.ActionEvent):
        code = event.params["code"]
        exec(code)  # noqa: S102

    def _on_collect_status(self, event: ops.CollectStatusEvent):
        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(SimpleCharm)
