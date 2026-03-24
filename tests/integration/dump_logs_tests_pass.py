"""This file is executed via test_dump_logs.py, it should not be run directly."""

from __future__ import annotations

import os
import pathlib
import typing

import jubilant
import pytest

if typing.TYPE_CHECKING:
    import pytest_jubilant


@pytest.fixture(scope="module")
def models(temp_model_factory: pytest_jubilant.TempModelFactory):
    foo = temp_model_factory.get_juju("foo1")
    bar = temp_model_factory.get_juju("bar1")
    yield foo, bar


@pytest.mark.setup
def test_deploy_and_pass(log_actions_charm: pathlib.Path, models: tuple[jubilant.Juju, jubilant.Juju]):
    foo, bar = models
    foo.deploy(log_actions_charm)
    bar.deploy(log_actions_charm)
    foo.wait(jubilant.all_active, timeout=900)
    bar.wait(jubilant.all_active)
    foo.run("simple/0", "log")
    bar.run("simple/0", "log")
