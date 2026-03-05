import unittest.mock

import pytest

import pytest_jubilant.main


def _patch_subprocess_run():
    mm = unittest.mock.MagicMock()
    mm.return_value = unittest.mock.MagicMock(stdout="output", stderr="error")
    return unittest.mock.patch("subprocess.run", new=mm)


@pytest.fixture(scope="session", autouse=True)
def _global_cli_mock():
    """Mock out subprocess.run for all tests."""
    pytest_jubilant.main._PYTESTING_RANDBITS_OVERRIDE = "testing"
    with _patch_subprocess_run():
        yield


@pytest.fixture(scope="module")
def cli_mock():
    """Mock out subprocess.run at the module level.

    This allows tests to inspect and assert on the calls made in their module scoped fixtures.
    Tests must request this fixture first (leftmost) so it runs before the fixtures under test do.
    """
    with _patch_subprocess_run() as mm:
        yield mm
