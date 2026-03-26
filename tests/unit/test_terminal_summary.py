from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = """
def test_something(juju):
    pass
"""


def test_default_shows_teardown_hint(pytester: pytest.Pytester):
    """When models are torn down (default), a hint to pass --no-teardown is shown."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "*Models were torn down*",
        "*--no-juju-teardown*",
    ])


def test_default_no_teardown_shows_rerun_hint(pytester: pytest.Pytester):
    """When --no-teardown is passed, a hint to rerun with the model prefix is shown."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-teardown")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "*Models were not torn down*",
        "--no-juju-setup --no-juju-teardown --juju-model jubilant-deadbeef",
    ])


def test_explicit_model_shows_teardown_hint(pytester: pytest.Pytester):
    """When --model is passed, a hint to pass --no-teardown is shown."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-model", "my-model")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "*Models were torn down*",
        "*--no-juju-teardown*",
    ])


def test_explicit_model_with_no_teardown_shows_rerun_hint(pytester: pytest.Pytester):
    """When --no-teardown is passed, a hint to rerun with the model prefix is shown."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-model", "my-model", "--no-juju-teardown")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "*Models were not torn down*",
        "--no-juju-setup --no-juju-teardown --juju-model my-model",
    ])
