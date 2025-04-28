#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""
import dataclasses
import logging
import secrets
import shlex
import subprocess
from pathlib import Path
from typing import Union, Optional, Dict
from urllib import request

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


@dataclasses.dataclass(frozen=True)
class ModelConfiguration:
    name: str
    keep_models: bool


@pytest.fixture(scope="module")
def root_model_configuration(request) -> ModelConfiguration:
    keep_models=request.config.getoption("--keep-models")

    if name := request.config.getoption("--model"):
        keep_models=True
    else:
        name = f"{request.module.__name__.rpartition(".")[-1]}+{secrets.token_hex(4)}"

    return ModelConfiguration(
        name=name,
        keep_models=keep_models
    )


def juju_client_with_model(model: str, keep_model=False, switch=False) -> jubilant.Juju:
    juju = jubilant.Juju()

    if not keep_model:
        juju.add_model(model)
    else:
        juju.model = model

    if switch:
        juju.cli("switch", model, include_model=False)

    return juju


@pytest.fixture(scope="module")
def juju(request, root_model_configuration):
    juju = juju_client_with_model(
        model=root_model_configuration.name,
        keep_model=root_model_configuration.keep_models,
        switch=request.config.getoption("--switch")
    )
    try:
        yield juju
    finally:
        if not root_model_configuration.keep_models:
            juju.destroy_model(root_model_configuration.name, destroy_storage=True, force=True)


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
    # FIXME: support multiple-charm outputs if there is more than one platform.
    charm = Path(proc.stderr.strip().splitlines()[-1].split()[-1])

    for meta_name in ("metadata.yaml", "charmcraft.yaml"):
        if (meta_yaml := Path(root) / meta_name).exists():
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
