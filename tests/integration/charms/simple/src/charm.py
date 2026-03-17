#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Minimal test charm for pack and deploy."""

import ops


class SimpleCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.collect_status, self._on_collect_status)

    def _on_collect_status(self, event: ops.CollectStatusEvent):
        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(SimpleCharm)
