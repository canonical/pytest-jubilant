"""Tests of the --dump-logs flag and logging related behaviour.

Named to run after the pack tests, as the test files use the packed charm.
"""

import pathlib

pytest_plugins = ["pytester"]

TEST_PASS = (pathlib.Path(__file__).parent / "dump_logs_tests_pass.py").read_text()
TEST_FAIL = (pathlib.Path(__file__).parent / "dump_logs_tests_fail.py").read_text()


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


def test_dump_logs_default_path(pytester):
    pytester.makepyfile(test_file=TEST_PASS)

    result = pytester.runpytest("--model", "model-t", "--dump-logs")

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    foo_log_path = pytester.path / ".logs" / "model-t-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = pytester.path / ".logs" / "model-t-bar-jdl.txt"
    assert bar_log_path.exists()


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

    foo_log_path = custom_dir / "model-t-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / "model-t-bar-jdl.txt"
    assert bar_log_path.exists()


def test_juju_debug_log_on_failure(pytester, tmp_path):
    pytester.makepyfile(test_file=TEST_FAIL)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "model-t", "--dump-logs", str(custom_dir))

    # We expect this session to fail.
    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("failed")

    # The full logs are still written on failure with --dump-logs.
    foo_log_path = custom_dir / "model-t-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / "model-t-bar-jdl.txt"
    assert bar_log_path.exists()

    # We emit the last 1000 lines of ``juju debug-log`` for each model if tests fail.
    # Model 'model-t-foo':
    foo_msg = "Logging last 1000 lines of ``juju debug-log`` for model model-t-foo:"
    foo_lines = result.stdout.get_lines_after(f"*{foo_msg}*")  # Match with fnmatch.
    for i, line in enumerate(foo_lines):
        if "Wrote full ``juju debug-log`` for model" in line:
            foo_end = i
            break
    else:  # no break
        print(foo_lines)
        assert False, "Didn't find expected message about writing the full log!"
    assert foo_end == 1000
    # Model 'model-t-bar':
    bar_msg = "Logging last 1000 lines of ``juju debug-log`` for model model-t-bar:"
    bar_lines = result.stdout.get_lines_after(f"*{bar_msg}*")  # Match with fnmatch.
    for i, line in enumerate(bar_lines):
        if "Wrote full ``juju debug-log`` for model" in line:
            bar_end = i
            break
    else:  # no break
        print(bar_lines)
        assert False, "Didn't find expected message about writing the full log!"
    assert bar_end == 1000
