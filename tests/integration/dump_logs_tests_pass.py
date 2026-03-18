"""This file is executed via test_NN_dump_logs.py, it should not be run directly."""

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
    foo = temp_model_factory.get_juju("foo")
    bar = temp_model_factory.get_juju("bar")
    yield foo, bar


@pytest.fixture(scope="module")
def charm():
    charm_path = pathlib.Path(os.environ["CHARM_PATH"])
    assert charm_path.is_file()
    yield charm_path


@pytest.mark.setup
def test_deploy(models: tuple[jubilant.Juju, jubilant.Juju], charm: pathlib.Path):
    foo, bar = models
    foo.deploy(charm)
    bar.deploy(charm)
    foo.wait(jubilant.all_active, timeout=900)
    bar.wait(jubilant.all_active)
