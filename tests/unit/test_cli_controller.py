from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = (Path(__file__).parent / "cli_controller_tests.py").read_text()


def test_cli_controller(pytester: pytest.Pytester):
    """``--juju-controller`` is used as model prefix, and can be overridden per get_juju() call."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-controller", "my-fancy-controller")

    result.assert_outcomes(passed=2)
