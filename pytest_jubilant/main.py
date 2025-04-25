#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""
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
        action="store_true",
        default=False,
        help="Skip model teardown.",
    )
    group.addoption(
        "--no-setup",
        action="store_true",
        default=False,
        help='Skip tests marked with "setup".',
    )
    group.addoption(
        "--no-teardown",
        action="store_true",
        default=False,
        help='Skip tests marked with "teardown".',
    )
    group.addoption(
        "--switch",
        action="store_true",
        default=False,
        help='Switch to the temporary model that is currently being worked on.',
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "setup: tests that setup some parts of the environment."
    )
    config.addinivalue_line(
        "markers", "teardown: tests that tear down some parts of the environment."
    )


def pytest_collection_modifyitems(config:pytest.Config, items):
    if config.getoption("--no-teardown"):
        skipper = pytest.mark.skip(reason="--no-teardown provided.")
        for item in items:
            if "teardown" in item.keywords:
                item.add_marker(skipper)

        if config.getoption("--keep-models"):
            logging.warning("--no-teardown implies --keep-models")
        else:
            # TODO: less hacky way to do this?
            optname = config._opt2dest.get("--keep-models", "--keep-models")  # noqa
            config.option.__setattr__(optname, True)

    if config.getoption("--no-setup"):
        skipper = pytest.mark.skip(reason="--no-setup provided.")
        for item in items:
            if "setup" in item.keywords:
                item.add_marker(skipper)


@pytest.fixture(scope="module")
def juju(request):
    switch = request.config.getoption("--switch")
    def _maybe_switch(juju):
        if switch:
            juju.cli("switch", model, include_model=False)
        return juju

    if model := request.config.getoption("--model"):
        juju = jubilant.Juju(model=model)
        yield _maybe_switch(juju)

    else:
        with jubilant.temp_model(
            keep=request.config.getoption("--keep-models")
        ) as juju:
            yield _maybe_switch(juju)


@dataclasses.dataclass
class _Result:
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
