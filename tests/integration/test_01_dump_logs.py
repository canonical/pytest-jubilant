"""Tests of the --dump-logs flag and logging related behaviour.

Named to run after the pack tests, as the test files use the packed charm.
"""

from __future__ import annotations

import pathlib

import pytest

pytest_plugins = ["pytester"]


@pytest.mark.parametrize("_", range(100))
def test_juju_debug_log_on_failure(_, pytester, tmp_path):
    test_file = (pathlib.Path(__file__).parent / "dump_logs_tests.py").read_text()
    pytester.makepyfile(test_file=test_file)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "model-t", "--dump-logs", str(custom_dir))

    # We expect this session to fail.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("failed")

    # We emit the last 1000 lines of `juju debug-log` for each model if tests fail.
    # Model 'model-t-foo': emits 10k lines of logs in an action and then fails.
    foo_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-foo:"
    foo_lines = result.stdout.get_lines_after(f"*{foo_msg}*")  # Match with fnmatch.
    foo_end = _index_contains(foo_lines, "Wrote full `juju debug-log` for model")
    assert foo_end == 1000
    foo_last_lines = foo_lines[:foo_end]
    assert _in_line("Hello, it is I! '10000'", foo_last_lines)
    assert not _in_line("Hello, it is I! '1'", foo_last_lines)  # We only log the last 1k lines.

    # Model 'model-t-bar': cleaned up when the tests exit after the action failed.
    bar_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-bar:"
    bar_lines = result.stdout.get_lines_after(f"*{bar_msg}*")  # Match with fnmatch.
    bar_end = _index_contains(bar_lines, "Wrote full `juju debug-log` for model")
    assert bar_end > 1
    assert bar_end < 1000  # We didn't run the log action so there aren't that many log lines.
    bar_last_lines = bar_lines[:bar_end]
    assert not _in_line("Hello, it is I!", bar_last_lines)  # We don't run the log action for bar.

    # The full logs are still written on failure with --dump-logs.
    foo_log_path = custom_dir / "model-t-foo-juju-debug.log"
    assert foo_log_path.exists()
    foo_full_log_lines = foo_log_path.read_text().splitlines()
    assert len(foo_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo_full_log_lines)
    bar_log_path = custom_dir / "model-t-bar-juju-debug.log"
    assert bar_log_path.exists()
    bar_full_log_lines = bar_log_path.read_text().splitlines()
    assert foo_full_log_lines
    assert not _in_line("Hello, it is I!", bar_full_log_lines)


def _index_contains(lines: list[str], target: str) -> int:
    for i, line in enumerate(lines):
        if target in line:
            return i
    raise ValueError(f"No match for {target!r} in {lines}")


def _in_line(target: str, lines: list[str]) -> bool:
    match = [line for line in lines if target in line]
    if not match:
        return False
    assert len(match) == 1, f"Expected only one match for {target} in but found {match}"
    return True
