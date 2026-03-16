from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_ALREADY_EXISTS = """
from typing import Any

import pytest
import pytest_jubilant
import jubilant


def _mock_add_model(self, model: str, *args: Any, **kwargs: Any):
    msg = (
        f'ERROR failed to create new model: '
        f'model "{model}" for admin already exists (already exists)'
    )
    raise jubilant.CLIError(1, ["juju", "add-model"], stderr=msg)


@pytest.fixture(scope="module", autouse=True)
def _patch_add_model():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "add_model", _mock_add_model)
        yield


def test_create_model(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("my-fancy-model")
""".strip()
TEST_OTHER_CLI_ERROR = """
from typing import Any

import pytest
import pytest_jubilant
import jubilant


def _mock_add_model(self, model: str, *args: Any, **kwargs: Any):
    raise jubilant.CLIError(1, ["juju", "add-model"], stderr="ERROR something else")


@pytest.fixture(scope="module", autouse=True)
def _patch_add_model():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "add_model", _mock_add_model)
        yield


def test_create_model(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("my-fancy-model")
""".strip()


def test_explicit_model_allows_collisions(pytester: pytest.Pytester):
    """If ``--model`` is set, an existing model error is allowed (and expected)."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_ALREADY_EXISTS)

    result = pytester.runpytest("--model", "my-fancy-model")

    result.assert_outcomes(passed=1)


def test_collision_without_explicit_model_raises(pytester: pytest.Pytester):
    """Without ``--model``, an existing model error is raised if there's a collision."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_ALREADY_EXISTS)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    module_name = "test-file"
    randbits = "testing"
    model_name = "my-fancy-model"
    msg = (
        "ERROR failed to create new model: "
        f'model "{module_name}-{randbits}-{model_name}" for admin already exists (already exists)'
    )
    assert msg in result.stdout.str()


def test_explicit_model_doesnt_prevent_other_errors(pytester: pytest.Pytester):
    """If ``--model`` is set, an existing model error is allowed (and expected)."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_OTHER_CLI_ERROR)

    result = pytester.runpytest("--model", "my-fancy-model")

    result.assert_outcomes(failed=1)
    assert "ERROR something else" in result.stdout.str()


def test_other_error_without_explicit_model_raises(pytester: pytest.Pytester):
    """Without ``--model``, an existing model error is raised if there's a collision."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_OTHER_CLI_ERROR)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    assert "ERROR something else" in result.stdout.str()
