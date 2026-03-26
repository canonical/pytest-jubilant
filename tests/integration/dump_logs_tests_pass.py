"""This file is executed via test_dump_logs.py, it should not be run directly."""

from __future__ import annotations

import typing

import jubilant
import pytest

if typing.TYPE_CHECKING:
    import pathlib

    import pytest_jubilant


@pytest.fixture(scope="module")
def models(juju_factory: pytest_jubilant.JujuFactory):
    foo = juju_factory.get_juju("foo1")
    bar = juju_factory.get_juju("bar1")
    yield foo, bar


@pytest.mark.setup
def test_deploy_and_pass(
    log_actions_charm: pathlib.Path, models: tuple[jubilant.Juju, jubilant.Juju]
):
    foo, bar = models
    foo.deploy(log_actions_charm, app="log")
    bar.deploy(log_actions_charm, app="log")
    foo.wait(jubilant.all_active, timeout=900)
    bar.wait(jubilant.all_active)
    foo.run("log/0", "log")
    bar.run("log/0", "log")
