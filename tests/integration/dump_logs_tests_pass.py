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
def models(juju_factory: pytest_jubilant.JujuFactory):
    foo = juju_factory.get_juju("foo1")
    bar = juju_factory.get_juju("bar1")
    yield foo, bar


@pytest.fixture(scope="module")
def charm():
    charm_path = pathlib.Path(os.environ["SIMPLE_CHARM_PATH"])
    assert charm_path.is_file()
    yield charm_path


@pytest.mark.juju_setup
def test_deploy_and_pass(models: tuple[jubilant.Juju, jubilant.Juju], charm: pathlib.Path):
    foo, bar = models
    foo.deploy(charm)
    bar.deploy(charm)
    foo.wait(jubilant.all_active, timeout=900)
    bar.wait(jubilant.all_active)
    foo.run("simple/0", "log")
    bar.run("simple/0", "log")
