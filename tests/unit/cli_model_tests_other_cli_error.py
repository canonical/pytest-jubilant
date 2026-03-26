"""This file is executed via test_cli_model.py, it should not be run directly."""

from typing import Any

import jubilant
import pytest

import pytest_jubilant


def _mock_add_model(self, model: str, *args: Any, **kwargs: Any):
    raise jubilant.CLIError(1, ["juju", "add-model"], stderr="ERROR something else")


@pytest.fixture(scope="module", autouse=True)
def _patch_add_model():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "add_model", _mock_add_model)
        yield


def test_create_model(juju_factory: pytest_jubilant.JujuFactory):
    juju_factory.get_juju("my-fancy-model")
