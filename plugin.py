import dataclasses
import logging
import shlex
import subprocess
from pathlib import Path
from typing import Union, Optional, Dict

import yaml
import pytest
import jubilant


def pytest_addoption(parser):
    group = parser.getgroup("jubilant")
    group.addoption(
        "--model",
        action="store",
        default=None,
        help="Juju model name to target.",
    )
    group.addoption(
        "--keep-models",
        action="store",
        default=None,
        help="Skip model teardown.",
    )
    group.addoption(
        "--no-setup",
        action="store",
        default=None,
        help='Skip tests marked with "setup".',
    )
    group.addoption(
        "--no-teardown",
        action="store",
        default=None,
        help='Skip tests marked with "teardown".',
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "setup: tests that setup some parts of the environment."
    )
    config.addinivalue_line(
        "markers", "teardown: tests that tear down some parts of the environment."
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--no-teardown"):
        skipper = pytest.mark.skip(reason="--no-teardown provided.")
        for item in items:
            if "teardown" in item.keywords:
                item.add_marker(skipper)

    if not config.getoption("--no-setup"):
        skipper = pytest.mark.skip(reason="--no-setup provided.")
        for item in items:
            if "setup" in item.keywords:
                item.add_marker(skipper)


@pytest.fixture(scope="module")
def juju(request):
    if model := request.config.getoption("--model"):
        yield jubilant.Juju(model=model)
    else:
        with jubilant.temp_model(
            keep=request.config.getoption("--keep-models")
        ) as juju:
            yield juju


class _Result(dataclasses.dataclass):
    charm: Path
    resources: Optional[Dict[str, str]]


def pack_charm(root: Union[Path, str] = "./") -> _Result:
    """Pack a local charm and return it along with its resources."""
    proc = subprocess.run(
        shlex.split(f"charmcraft pack -p {root}"),
        check=True,
        capture_output=True,
        text=True,
    )

    # Don't ask me why this goes to stderr.
    charm = proc.stderr.strip().splitlines()[-1].split()[-1]

    for meta_name in ("metadata.yaml", "charmcraft.yaml"):
        if (meta_yaml := root / meta_name).exists():
            logging.debug(f"found metadata file: {meta_yaml}")
            meta = yaml.safe_load(meta_yaml.read_text())
            resources = {
                resource: res_meta["upstream-source"]
                for resource, res_meta in meta["resources"].items()
            }
            break
    else:
        resources = None
        logging.error(
            f"metadata/charmcraft.yaml not found at {root}; unable to load resources"
        )

    return _Result(charm=charm, resources=resources)
