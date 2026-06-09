import os
import pathlib

import pytest


@pytest.fixture(scope="session")
def smoke_charm():
    charm_path = os.environ.get("SMOKE_CHARM_PATH")
    if not charm_path:
        raise RuntimeError("SMOKE_CHARM_PATH environment variable is not set")
    charm_path = pathlib.Path(charm_path)
    if not charm_path.exists():
        raise FileNotFoundError(f"charm not found at {charm_path}")
    return charm_path.absolute()


@pytest.fixture(scope="session")
def log_actions_charm():
    charm_path = os.environ.get("LOG_ACTIONS_CHARM_PATH")
    if not charm_path:
        raise RuntimeError("LOG_ACTIONS_CHARM_PATH environment variable is not set")
    charm_path = pathlib.Path(charm_path)
    if not charm_path.exists():
        raise FileNotFoundError(f"charm not found at {charm_path}")
    return charm_path.absolute()


@pytest.fixture(scope="session")
def juju_controller():
    return os.environ.get("JUJU_CONTROLLER", "concierge-lxd")
