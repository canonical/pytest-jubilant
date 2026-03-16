"""This file is executed via test_cli_markers.py, it should not be run directly."""

from pathlib import Path
from typing import Any

import jubilant
import pytest

import pytest_jubilant

TMP_PATH = "### REGEX SUBSTUTION TARGET ###"
if TMP_PATH == "### REGEX SUBSTUTION TARGET ###":
    raise ValueError("The value of TMP_PATH must be substituted before running.")


def _append(path: Path, model: str) -> None:
    if path.exists():
        with path.open("a") as f:
            f.write(f"\n{model}")
    else:
        path.write_text(f"{model}")


def _mock_add(self, model, *args: Any, **kwargs: Any):
    _append(Path(TMP_PATH) / "added.txt", model)


def _mock_destroy(self, model, *args: Any, **kwargs: Any):
    _append(Path(TMP_PATH) / "destroyed.txt", model)


@pytest.fixture(scope="module", autouse=True)
def _patch_model_operations():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "add_model", _mock_add)
        monkeypatch.setattr(jubilant.Juju, "destroy_model", _mock_destroy)
        yield


@pytest.mark.setup
def test_setup(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("setup")


def test_regular(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("regular")


@pytest.mark.teardown
def test_teardown(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("teardown")
