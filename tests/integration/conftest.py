import os
import pathlib

import pytest


@pytest.fixture(scope="session")
def simple_charm():
    charm_path = os.environ.get("SIMPLE_CHARM_PATH")
    if not charm_path:
        raise RuntimeError("SIMPLE_CHARM_PATH environment variable is not set")
    charm_path = pathlib.Path(charm_path)
    if not charm_path.exists():
        raise FileNotFoundError(f"charm not found at {charm_path}")
    return charm_path.absolute()
