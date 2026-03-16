import re
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = (Path(__file__).parent / "cli_markers_tests.py").read_text()
REGEX_TARGET = "### REGEX SUBSTUTION TARGET ###"


def test_default(pytester: pytest.Pytester, tmp_path: Path):
    """By default, all tests are run, and all models are torn down."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-file-testing-setup",
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-file-testing-setup",
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]


def test_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-setup`` means tests marked ``setup`` aren't run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("--no-setup")

    result.assert_outcomes(passed=2, skipped=1)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]


def test_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-teardown`` means tests marked ``teardown`` aren't run, and models aren't torn down"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("--no-teardown")

    result.assert_outcomes(passed=2, skipped=1)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-file-testing-setup",
        "test-file-testing-regular",
    ]
    assert not (tmp_path / "destroyed.txt").exists()


def test_no_setup_and_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``--no-setup`` and ``--no-teardown`` both being passed means neither are run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("--no-setup", "--no-teardown")

    result.assert_outcomes(passed=1, skipped=2)
    assert (tmp_path / "added.txt").read_text() == "test-file-testing-regular"
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` only runs tests marked ``setup``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("-m", "setup")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text() == "test-file-testing-setup"
    assert (tmp_path / "destroyed.txt").read_text() == "test-file-testing-setup"


def test_m_setup_with_no_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` + ``--no-teardown`` means only ``setup`` tests run + models aren't torn down"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("-m", "setup", "--no-teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text() == "test-file-testing-setup"
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_setup_with_no_setup(pytester: pytest.Pytester, tmp_path: Path):
    """``-m setup`` and ``--no-setup`` mean no tests are run"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("-m", "setup", "--no-setup")

    result.assert_outcomes(skipped=1, deselected=2)
    assert not (tmp_path / "added.txt").exists()
    assert not (tmp_path / "destroyed.txt").exists()


def test_m_teardown(pytester: pytest.Pytester, tmp_path: Path):
    """``-m teardown`` only runs tests marked ``teardown``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("-m", "teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (tmp_path / "added.txt").read_text() == "test-file-testing-teardown"
    assert (tmp_path / "destroyed.txt").read_text() == "test-file-testing-teardown"


def test_keep_models_is_unknown(pytester: pytest.Pytester):
    """``pytest-jubilant`` doesn't define ``--keep-models``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file="def test_ok(): assert True")

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
    pytester.makepyfile(test_file=re.sub(REGEX_TARGET, str(tmp_path), TEST_FILE, count=1))

    result = pytester.runpytest("--keep-models")

    result.assert_outcomes(passed=3)
    assert (tmp_path / "added.txt").read_text().splitlines() == [
        "test-file-testing-setup",
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]
    assert (tmp_path / "destroyed.txt").read_text().splitlines() == [
        "test-file-testing-setup",
        "test-file-testing-regular",
        "test-file-testing-teardown",
    ]
