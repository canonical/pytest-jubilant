from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_MARKERS = """
from pathlib import Path
from typing import Any

import pytest
import pytest_jubilant
import jubilant


def _append(path: Path, model: str) -> None:
    if path.exists():
        path.write_text(f"{{path.read_text()}}\\n{{model}}")
    else:
        path.write_text(f"{{model}}")


def _mock_add(self, model, *args: Any, **kwargs: Any):
    _append(Path("{tmp_path}") / "added.txt", model)


def _mock_destroy(self, model, *args: Any, **kwargs: Any):
    _append(Path("{tmp_path}") / "destroyed.txt", model)


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
""".strip()


def test_default(pytester: pytest.Pytester, tmp_path: Path):
    """By default, all tests are run, and all models are torn down."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]


def test_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-setup`` means tests marked ``setup`` aren't run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("--no-setup")

    result.assert_outcomes(passed=2, skipped=1)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]


def test_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-teardown`` means tests marked ``teardown`` aren't run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("--no-teardown")

    result.assert_outcomes(passed=2, skipped=1)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
    ]
    assert not (tmp_path / "destroyed.txt").exists()


def test_no_setup_and_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-setup`` and ``--no-teardown`` both being passed means neither are run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("--no-setup", "--no-teardown")

    result.assert_outcomes(passed=1, skipped=2)
    assert (tmp_path / "added.txt").read_text().splitlines() == ["test-sample-testing-regular"]
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` only runs tests marked ``setup``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("-m", "setup")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text().splitlines() == ["test-sample-testing-setup"]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == ["test-sample-testing-setup"]


def test_m_setup_with_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` + ``--no-teardown`` means only ``setup`` tests run + models aren't torn down"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("-m", "setup", "--no-teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text().splitlines() == ["test-sample-testing-setup"]
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_setup_with_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` and ``--no-setup`` mean no tests are run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("-m", "setup", "--no-setup")

    result.assert_outcomes(skipped=1, deselected=2)
    assert not (tmp_path / "added.txt").exists()
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``-m teardown`` only runs tests marked ``teardown``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("-m", "teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text().splitlines() == ["test-sample-testing-teardown"]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-sample-testing-teardown"
    ]


def test_keep_models_is_unknown(pytester: pytest.Pytester):
    """``pytest-jubilant`` doesn't define ``--keep-models``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample="def test_ok(): assert True")

    result = pytester.runpytest("--keep-models")

    assert result.ret != 0
    assert any("--keep-models" in line for line in result.errlines)


def test_keep_models_is_ignored(pytester: pytest.Pytester, tmp_path: Path):
    """If a user defines ``--keep-models``, we don't respect it."""
    keep_models_conftest = f"""
{CONFTEST}


def pytest_addoption(parser):
    parser.addoption("--keep-models", action="store_true", default=False)
""".strip()
    pytester.makeconftest(keep_models_conftest)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path))

    result = pytester.runpytest("--keep-models")

    result.assert_outcomes(passed=3)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]
