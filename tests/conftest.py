import os
import pytest

# do this on module import; doing it in a fixture would be already too late, because the patch
# needs to be applied before the tempmodelfactory is invoked.
os.environ["PYTESTING_PYTEST_JUBILANT"] = "1"


@pytest.fixture(scope="session", autouse=True)
def _cleanup_testing_envvar():
    yield
    del os.environ["PYTESTING_PYTEST_JUBILANT"]
