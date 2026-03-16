from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_SAMPLE = """
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
    temp_model_factory.get_juju("testing")
""".strip()


def test_allow_existing_model(pytester: pytest.Pytester):
    """If ``--model`` is set, an existing model error is allowed (and expected)."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_SAMPLE)

    result = pytester.runpytest("--model", "testing")

    result.assert_outcomes(passed=1)


def test_disallow_existing_model(pytester: pytest.Pytester):
    """Without ``--model``, an existing model error is raised if there's a collision."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_SAMPLE)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
