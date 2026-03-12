import unittest.mock

import pytest


@pytest.fixture(scope="session", autouse=True)
def _global_random_bits_mock():
    """Mock out secrets.token_hex so we can have predictable model names."""
    with unittest.mock.patch("secrets.token_hex", new=lambda _: "testing"):
        yield


@pytest.fixture(scope="session", autouse=True)
def _global_cli_mock():
    """Mock out subprocess.run for all tests."""
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


def _patch_subprocess_run():
    mm = unittest.mock.MagicMock()
    mm.return_value = unittest.mock.MagicMock(stdout="output", stderr="error")
    return unittest.mock.patch("subprocess.run", new=mm)
