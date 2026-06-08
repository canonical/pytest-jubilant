from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = (Path(__file__).parent / "cli_cloud_tests.py").read_text()


def test_cli_cloud(pytester: pytest.Pytester):
    """``--juju-cloud`` is used as juju argument, and can be overridden per get_juju() call."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-cloud", "my-fancy-cloud")

    result.assert_outcomes(passed=2)
