"""Tests of the --dump-logs flag and logging related behaviour.

Named to run after the pack tests, as the test files use the packed charm.
"""

from __future__ import annotations

import pathlib

import pytest

pytest_plugins = ["pytester"]

TEST_PASS = (pathlib.Path(__file__).parent / "dump_logs_tests_pass.py").read_text()
TEST_FAIL = (pathlib.Path(__file__).parent / "dump_logs_tests_fail.py").read_text()


@pytest.mark.skip()
def test_no_dump_logs(pytester):
    pytester.makepyfile(test_file=TEST_PASS)

    result = pytester.runpytest()

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    assert not (pytester.path / ".logs").exists()


@pytest.mark.skip()
def test_dump_logs_default_path(pytester):
    pytester.makepyfile(test_file=TEST_PASS)

    result = pytester.runpytest("--model", "model-t", "--dump-logs")

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    foo_log_path = pytester.path / ".logs" / "model-t-foo-juju-debug.log"
    assert foo_log_path.exists()
    bar_log_path = pytester.path / ".logs" / "model-t-bar-juju-debug.log"
    assert bar_log_path.exists()


@pytest.mark.skip()
def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makepyfile(test_file=TEST_PASS)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "model-t", "--dump-logs", str(custom_dir))

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    foo_log_path = custom_dir / "model-t-foo-juju-debug.log"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / "model-t-bar-juju-debug.log"
    assert bar_log_path.exists()


def test_juju_debug_log_on_failure(pytester, tmp_path):
    pytester.makepyfile(test_file=TEST_FAIL)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "model-t", "--dump-logs", str(custom_dir))

    # We expect this session to fail.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("failed")

    # We emit the last 1000 lines of ``juju debug-log`` for each model if tests fail.
    # We log the last 1000 if present, but our tests aren't very long,
    # and the linecount depends on external factors like how long we waited for active,
    # so we just assert that we logged something.
    # Model 'model-t-foo':
    foo_msg = "Logging last 1000 lines of ``juju debug-log`` for model model-t-foo:"
    foo_lines = result.stdout.get_lines_after(f"*{foo_msg}*")  # Match with fnmatch.
    foo_end = _index_contains(foo_lines, "Wrote full ``juju debug-log`` for model")
    assert foo_end > 1
    foo_last_lines = foo_lines[:foo_end]
    assert _in_line("Hello, it is I! '10000'", foo_last_lines)
    assert not _in_line("Hello, it is I! '1'", foo_last_lines)  # we only log the last 1k lines
    # Model 'model-t-bar':
    bar_msg = "Logging last 1000 lines of ``juju debug-log`` for model model-t-bar:"
    bar_lines = result.stdout.get_lines_after(f"*{bar_msg}*")  # Match with fnmatch.
    bar_end = _index_contains(bar_lines, "Wrote full ``juju debug-log`` for model")
    assert bar_end > 1
    bar_last_lines = bar_lines[:bar_end]
    assert _in_line("Hello, it is I! '10000'", bar_last_lines)
    assert not _in_line("Hello, it is I! '1'", bar_last_lines)  # we only log the last 1k lines

    # The full logs are still written on failure with --dump-logs.
    foo_log_path = custom_dir / "model-t-foo-juju-debug.log"
    assert foo_log_path.exists()
    foo_full_log_lines = foo_log_path.read_text().splitlines()
    assert _in_line("Hello, it is I! '1'", foo_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo_full_log_lines)
    bar_log_path = custom_dir / "model-t-bar-juju-debug.log"
    assert bar_log_path.exists()
    bar_full_log_lines = bar_log_path.read_text().splitlines()
    assert _in_line("Hello, it is I! '1'", bar_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", bar_full_log_lines)


def _index_contains(lines: list[str], target: str) -> int:
    for i, line in enumerate(lines):
        if target in line:
            return i
    raise ValueError(f"No match for {target!r} in {lines}")


def _in_line(target: str, lines: list[str]) -> bool:
    match = [line for line in lines if target in line]
    if not match:
        return False
    assert len(match) == 1, f"Expected only one match for {target} in {lines}"
    return True
