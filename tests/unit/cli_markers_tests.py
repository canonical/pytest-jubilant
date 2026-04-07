"""This file is executed via test_cli_markers.py, it should not be run directly."""

from pathlib import Path
from typing import Any

import jubilant
import pytest

import pytest_jubilant


def _append(path: Path, model: str) -> None:
    if path.exists():
        with path.open("a") as f:
            f.write(f"\n{model}")
    else:
        path.write_text(f"{model}")


def _mock_add(self, model, *args: Any, **kwargs: Any):
    _append(Path("added.txt"), model)


def _mock_destroy(self, model, *args: Any, **kwargs: Any):
    _append(Path("destroyed.txt"), model)


# Session scoped fixture so patching wraps our module scoped autouse fixture.
@pytest.fixture(scope="session", autouse=True)
def _patch_model_operations():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "add_model", _mock_add)
        monkeypatch.setattr(jubilant.Juju, "destroy_model", _mock_destroy)
        yield


@pytest.fixture(scope="module", autouse=True)
def _fixture(juju_factory: pytest_jubilant.JujuFactory):
    juju_factory.get_juju("autouse-module-scoped-fixture")


@pytest.mark.juju_setup
def test_setup(juju_factory: pytest_jubilant.JujuFactory):
    juju_factory.get_juju("setup")


def test_regular(juju_factory: pytest_jubilant.JujuFactory):
    juju_factory.get_juju("regular")


@pytest.mark.juju_teardown
def test_teardown(juju_factory: pytest_jubilant.JujuFactory):
    juju_factory.get_juju("teardown")
