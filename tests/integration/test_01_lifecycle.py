import pathlib
import secrets
import shutil

import pytest

import pytest_jubilant

TEST_FILE = (pathlib.Path(__file__).parent / 'lifecycle_tests.py').read_text()


def test_dump_logs_not_passed(pytester):
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest()

    outcomes = result.parseoutcomes()
    assert outcomes["failed"] == 0
    assert outcomes["errors"] == 0
    assert outcomes["warnings"] == 0

    assert not (pytester.path / '.logs').exists()


def test_dump_logs_default_path(pytester):
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--model", "modelt", "--dump-logs")

    outcomes = result.parseoutcomes()
    assert outcomes["failed"] == 0
    assert outcomes["errors"] == 0
    assert outcomes["warnings"] == 0

    foo_log_path = pytester.path / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = pytester.path / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "modelt", "--dump-logs", str(custom_dir))

    outcomes = result.parseoutcomes()
    assert outcomes["failed"] == 0
    assert outcomes["errors"] == 0
    assert outcomes["warnings"] == 0

    foo_log_path = custom_dir / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()
