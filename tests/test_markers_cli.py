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
        path.write_text(path.read_text() + f"\\n{{model}}")
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


TEST_KEEP_MODELS = """
from pathlib import Path
from typing import Any

import pytest
import pytest_jubilant
import jubilant


def _mock_destroy(self, model, *args: Any, **kwargs: Any):
    Path("{tmp_file}").write_text(model)


@pytest.fixture(scope="module", autouse=True)
def _patch_destroy_model():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(jubilant.Juju, "destroy_model", _mock_destroy)
        yield


def test_keep_models_option_ignored(temp_model_factory: pytest_jubilant.TempModelFactory):
    temp_model_factory.get_juju("foo")
""".strip()


def _read_log(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.exists() else []


def test_no_teardown_skips_teardown_markers(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("--no-teardown")

    result.assert_outcomes(passed=2, skipped=1)
    assert _read_log(tmp_path / "added.txt") == [
        "test-sample-testing-setup",
        "test-sample-testing-regular",
    ]
    assert _read_log(tmp_path / "destroyed.txt") == []


def test_no_setup_skips_setup_markers(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("--no-setup")

    result.assert_outcomes(passed=2, skipped=1)
    assert _read_log(tmp_path / "added.txt") == [
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]
    assert _read_log(tmp_path / "destroyed.txt") == [
        "test-sample-testing-regular",
        "test-sample-testing-teardown",
    ]


def test_no_setup_and_no_teardown_skips_both_markers(
    pytester: pytest.Pytester,
    tmp_path: Path,
):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("--no-setup", "--no-teardown")

    result.assert_outcomes(passed=1, skipped=2)
    assert _read_log(tmp_path / "added.txt") == ["test-sample-testing-regular"]
    assert _read_log(tmp_path / "destroyed.txt") == []


def test_marker_selection_setup_only(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "setup")

    result.assert_outcomes(passed=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == ["test-sample-testing-setup"]
    assert _read_log(tmp_path / "destroyed.txt") == ["test-sample-testing-setup"]


def test_marker_selection_teardown_only(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == ["test-sample-testing-teardown"]
    assert _read_log(tmp_path / "destroyed.txt") == ["test-sample-testing-teardown"]


def test_marker_setup_with_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "setup", "--no-setup")

    result.assert_outcomes(skipped=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == []
    assert _read_log(tmp_path / "destroyed.txt") == []


def test_marker_setup_with_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "setup", "--no-teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == ["test-sample-testing-setup"]
    assert _read_log(tmp_path / "destroyed.txt") == []


def test_marker_teardown_with_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "teardown", "--no-teardown")

    result.assert_outcomes(skipped=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == []
    assert _read_log(tmp_path / "destroyed.txt") == []


def test_marker_teardown_with_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS.format(tmp_path=tmp_path.as_posix()))

    result = pytester.runpytest("-m", "teardown", "--no-setup")

    result.assert_outcomes(passed=1, deselected=2)
    assert _read_log(tmp_path / "added.txt") == ["test-sample-testing-teardown"]
    assert _read_log(tmp_path / "destroyed.txt") == ["test-sample-testing-teardown"]


def test_keep_models_option_is_unknown(pytester: pytest.Pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample="def test_ok(): assert True")

    result = pytester.runpytest("--keep-models")

    assert result.ret != 0
    assert any("--keep-models" in line for line in result.errlines)


def test_keep_models_option_is_ignored(pytester: pytest.Pytester, tmp_path: Path):
    keep_models_conftest = f"""
{CONFTEST}


def pytest_addoption(parser):
    parser.addoption("--keep-models", action="store_true", default=False)
""".strip()
    destroy_log = tmp_path / "destroyed.txt"
    test_sample = TEST_KEEP_MODELS.format(tmp_file=destroy_log.as_posix())

    pytester.makeconftest(keep_models_conftest)
    pytester.makepyfile(test_sample=test_sample)

    result = pytester.runpytest("--keep-models")

    result.assert_outcomes(passed=1)
    assert destroy_log.exists()
    assert destroy_log.read_text() == "test-sample-testing-foo"
