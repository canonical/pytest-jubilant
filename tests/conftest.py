import unittest.mock

import pytest

import pytest_jubilant.main


# Executed by pytest before any test runs -- so before any fixtures are requested.
# We need to patch now, before the library's fixtures are invoked, as we're testing those fixtures.

# 1) _PYTESTING_RANDBITS_OVERRIDE
pytest_jubilant.main._PYTESTING_RANDBITS_OVERRIDE = "testing"


# 2) mock subprocess.run globally for all tests
def _patch_subprocess_run():
    mm = unittest.mock.MagicMock()
    mm.return_value = unittest.mock.MagicMock(stdout="output", stderr="error")
    return unittest.mock.patch("subprocess.run", new=mm)


_GLOBAL_SUBPROCESS_PATCHER = _patch_subprocess_run()
_GLOBAL_SUBPROCESS_PATCHER.start()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_global_cli_mock():
    yield
    _GLOBAL_SUBPROCESS_PATCHER.stop()


# 3) Re-mock at module scope so that we can inspect the calls in the tests.
# Must be module rather than function scope as we're testing behaviour of module scoped fixtures.
# Tests must request cli_mock first (leftmost) so it runs before the fixtures under test.
@pytest.fixture(scope="module")
def cli_mock():
    with _patch_subprocess_run() as mm:
        yield mm
