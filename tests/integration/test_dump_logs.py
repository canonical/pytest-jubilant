"""Tests of the --dump-logs flag and logging related behaviour."""

from __future__ import annotations

import pathlib
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

    import pytest

pytest_plugins = ["pytester"]

CONFTEST = (pathlib.Path(__file__).parent / "conftest.py").read_text()


def test_juju_debug_log_on_fail(pytester: pytest.Pytester, tmp_path: pathlib.Path):
    test_file1 = (pathlib.Path(__file__).parent / "dump_logs_tests_fail.py").read_text()
    test_file2 = test_file1.replace('get_juju("foo1")', 'get_juju("foo2")')
    test_file2 = test_file2.replace('get_juju("bar1")', 'get_juju("bar2")')
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file1=test_file1, test_file2=test_file2)  # type: ignore
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest_subprocess(
        "--juju-model", "model-t", "--juju-dump-logs", str(custom_dir)
    )

    # We expect this session to fail.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("failed") == 2

    # test_file1
    # The full logs are still written on failure with --dump-logs.
    foo1_log_path = custom_dir / "model-t-test-file1-foo1-juju-debug.log"
    assert foo1_log_path.exists()
    foo1_full_log_lines = foo1_log_path.read_text().splitlines()
    assert len(foo1_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo1_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo1_full_log_lines)
    bar1_log_path = custom_dir / "model-t-test-file1-bar1-juju-debug.log"
    assert bar1_log_path.exists()
    bar1_full_log_lines = bar1_log_path.read_text().splitlines()
    assert bar1_full_log_lines
    assert not _in_line("Hello, it is I!", bar1_full_log_lines)

    # test_file2
    # The full logs are still written on failure with --dump-logs.
    foo2_log_path = custom_dir / "model-t-test-file2-foo2-juju-debug.log"
    assert foo2_log_path.exists()
    foo2_full_log_lines = foo2_log_path.read_text().splitlines()
    assert len(foo2_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo2_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo2_full_log_lines)
    bar2_log_path = custom_dir / "model-t-test-file2-bar2-juju-debug.log"
    assert bar2_log_path.exists()
    bar2_full_log_lines = bar2_log_path.read_text().splitlines()
    assert bar2_full_log_lines
    assert not _in_line("Hello, it is I!", bar2_full_log_lines)


def test_juju_debug_log_on_pass(pytester: pytest.Pytester, tmp_path: pathlib.Path):
    test_file1 = (pathlib.Path(__file__).parent / "dump_logs_tests_pass.py").read_text()
    test_file2 = test_file1.replace('get_juju("foo1")', 'get_juju("foo2")')
    test_file2 = test_file2.replace('get_juju("bar1")', 'get_juju("bar2")')
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file1=test_file1, test_file2=test_file2)  # type: ignore
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest_subprocess(
        "--juju-model", "model-t", "--juju-dump-logs", str(custom_dir)
    )

    # We expect this session to pass.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed") == 2
    assert "failed" not in outcomes

    # The full logs are still written with --dump-logs even on success.
    foo1_log_path = custom_dir / "model-t-test-file1-foo1-juju-debug.log"
    assert foo1_log_path.exists()
    foo1_full_log_lines = foo1_log_path.read_text().splitlines()
    assert len(foo1_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo1_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo1_full_log_lines)
    bar1_log_path = custom_dir / "model-t-test-file1-bar1-juju-debug.log"
    assert bar1_log_path.exists()
    bar1_full_log_lines = bar1_log_path.read_text().splitlines()
    assert len(bar1_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", bar1_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", bar1_full_log_lines)

    # test_file2
    foo2_log_path = custom_dir / "model-t-test-file2-foo2-juju-debug.log"
    assert foo2_log_path.exists()
    foo2_full_log_lines = foo2_log_path.read_text().splitlines()
    assert len(foo2_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", foo2_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", foo2_full_log_lines)
    bar2_log_path = custom_dir / "model-t-test-file2-bar2-juju-debug.log"
    assert bar2_log_path.exists()
    bar2_full_log_lines = bar2_log_path.read_text().splitlines()
    assert len(bar2_full_log_lines) > 10_000  # log action logs 10k times
    assert _in_line("Hello, it is I! '1'", bar2_full_log_lines)
    assert _in_line("Hello, it is I! '10000'", bar2_full_log_lines)


def _in_line(target: str, lines: Iterable[str]) -> bool:
    match = [line for line in lines if target in line]
    if not match:
        return False
    assert len(match) == 1, f"Expected only one match for {target} in but found {match}"
    return True
