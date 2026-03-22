"""Tests of the --dump-logs flag and logging related behaviour.

Named to run after the pack tests, as the test files use the packed charm.
"""

from __future__ import annotations

import pathlib

import pytest

pytest_plugins = ["pytester"]


@pytest.mark.parametrize("_", range(100))
def test_juju_debug_log_on_failure(_, pytester: pytest.Pytester, tmp_path: pathlib.Path):
    test_file1 = (pathlib.Path(__file__).parent / "dump_logs_tests.py").read_text()
    test_file2 = test_file1.replace('get_juju("foo1")', 'get_juju("foo2")')
    test_file2 = test_file2.replace('get_juju("bar1")', 'get_juju("bar2")')
    pytester.makepyfile(test_file1=test_file1, test_file2=test_file2)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "model-t", "--dump-logs", str(custom_dir))

    # We expect this session to fail.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("failed") == 2

    # test_file1
    # We emit the last 1000 lines of `juju debug-log` for each model if tests fail.
    # Model 'model-t-foo1': emits 10k lines of logs in an action and then fails.
    foo1_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-foo1:"
    foo1_lines = result.stdout.get_lines_after(f"*{foo1_msg}*")  # Match with fnmatch.
    foo1_end = _index_contains(foo1_lines, "Wrote full `juju debug-log` for model")
    assert foo1_end == 1000
    foo1_last_lines = foo1_lines[:foo1_end]
    assert _in_line("Hello, it is I! '10000'", foo1_last_lines)
    assert not _in_line("Hello, it is I! '1'", foo1_last_lines)  # We only log the last 1k lines.

    # Model 'model-t-bar1': cleaned up when the tests exit after the action failed.
    bar1_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-bar1:"
    bar1_lines = result.stdout.get_lines_after(f"*{bar1_msg}*")  # Match with fnmatch.
    bar1_end = _index_contains(bar1_lines, "Wrote full `juju debug-log` for model")
    assert bar1_end > 1
    assert bar1_end < 1000  # We didn't run the log action so there aren't that many log lines.
    bar1_last_lines = bar1_lines[:bar1_end]
    assert not _in_line("Hello, it is I!", bar1_last_lines)  # We don't run the log action for bar.

    # The full logs are still written on failure with --dump-logs.
    foo1_log_path = custom_dir / "model-t-foo1-juju-debug.log"
    assert foo1_log_path.exists()
    foo1_full_log_lines = foo1_log_path.read_text().splitlines()
    assert len(foo1_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo1_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo1_full_log_lines)
    bar1_log_path = custom_dir / "model-t-bar1-juju-debug.log"
    assert bar1_log_path.exists()
    bar1_full_log_lines = bar1_log_path.read_text().splitlines()
    assert bar1_full_log_lines
    assert not _in_line("Hello, it is I!", bar1_full_log_lines)

    # test_file2
    # We emit the last 1000 lines of `juju debug-log` for each model if tests fail.
    # Model 'model-t-foo2': emits 10k lines of logs in an action and then fails.
    foo2_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-foo2:"
    foo2_lines = result.stdout.get_lines_after(f"*{foo2_msg}*")  # Match with fnmatch.
    foo2_end = _index_contains(foo2_lines, "Wrote full `juju debug-log` for model")
    assert foo2_end == 1000
    foo2_last_lines = foo2_lines[:foo2_end]
    assert _in_line("Hello, it is I! '10000'", foo2_last_lines)
    assert not _in_line("Hello, it is I! '1'", foo2_last_lines)  # We only log the last 1k lines.

    # Model 'model-t-bar2': cleaned up when the tests exit after the action failed.
    bar2_msg = "Logging last 1000 lines of `juju debug-log` for model model-t-bar2:"
    bar2_lines = result.stdout.get_lines_after(f"*{bar2_msg}*")  # Match with fnmatch.
    bar2_end = _index_contains(bar2_lines, "Wrote full `juju debug-log` for model")
    assert bar2_end > 1
    assert bar2_end < 1000  # We didn't run the log action so there aren't that many log lines.
    bar2_last_lines = bar2_lines[:bar2_end]
    assert not _in_line("Hello, it is I!", bar2_last_lines)  # We don't run the log action for bar.

    # The full logs are still written on failure with --dump-logs.
    foo2_log_path = custom_dir / "model-t-foo2-juju-debug.log"
    assert foo2_log_path.exists()
    foo2_full_log_lines = foo2_log_path.read_text().splitlines()
    assert len(foo2_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo2_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo2_full_log_lines)
    bar2_log_path = custom_dir / "model-t-bar2-juju-debug.log"
    assert bar2_log_path.exists()
    bar2_full_log_lines = bar2_log_path.read_text().splitlines()
    assert bar2_full_log_lines
    assert not _in_line("Hello, it is I!", bar2_full_log_lines)


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
