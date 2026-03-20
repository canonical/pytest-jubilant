#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""

from __future__ import annotations

import dataclasses
import logging
import secrets
import shlex
import subprocess
from pathlib import Path

import jubilant
import pytest
import yaml

JDL_LOGFILE_EXTENSION = "-jdl.txt"
DEFAULT_JDL_DUMP_PATH = "./.logs"


def pytest_addoption(parser):
    group = parser.getgroup("jubilant")
    group.addoption(
        "--model",
        action="store",
        default=None,
        help="Juju model name to target.",
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
        help="Switch to the temporary model that is currently being worked on.",
    )
    group.addoption(
        "--dump-logs",
        action="store",
        nargs="?",
        const=DEFAULT_JDL_DUMP_PATH,
        default=None,
        help="Dump the juju debug-log for each model prior to teardown. "
        f"The default dump location is {DEFAULT_JDL_DUMP_PATH!r}.",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "setup: tests that setup some parts of the environment.")
    config.addinivalue_line(
        "markers", "teardown: tests that tear down some parts of the environment."
    )
    if config.getoption("--no-setup") and not config.getoption("--model"):
        msg = (
            "--no-setup cannot be specified without --model"
            ", because --no-setup will skip model creation"
            ", and surely your tests need a model."
        )
        if not config.getoption("--no-teardown"):
            msg += (
                "\nNote that unless you specify --no-teardown"
                ", the model(s) identified by --model *will* be torn down!"
            )
        raise pytest.UsageError(msg)


def pytest_collection_modifyitems(config: pytest.Config, items):
    if config.getoption("--no-teardown"):
        skipper = pytest.mark.skip(reason="--no-teardown provided.")
        for item in items:
            if "teardown" in item.keywords:
                item.add_marker(skipper)

    if config.getoption("--no-setup"):
        skipper = pytest.mark.skip(reason="--no-setup provided.")
        for item in items:
            if "setup" in item.keywords:
                item.add_marker(skipper)


class TempModelFactory:
    """Manages temporary models for testing."""

    def __init__(
        self,
        prefix: str,
        randbits: str | None = None,
        allow_existing_model: bool = False,
        add_model: bool = False,
    ):
        self.prefix = prefix
        self.randbits = randbits
        self._models: dict[str, jubilant.Juju] = {}
        self._allow_existing_model = allow_existing_model
        self._add_model = add_model

    def get_juju(self, suffix: str) -> jubilant.Juju:
        model_name = "-".join(filter(None, (self.prefix, self.randbits, suffix)))
        if model_name in self._models:
            raise ValueError(
                f"model {model_name} already registered on this temp_model factory. "
                "choose a different prefix."
            )

        juju = jubilant.Juju(model=model_name)
        if self._add_model:
            try:
                juju.add_model(model_name)
            except jubilant.CLIError as e:
                # If --model is set (_allow_existing_model is True), then the user wants collisions.
                # If the name is randomly generated, the chance of colliding with another
                # randomly generated model that wasn't torn down is tiny, so we we'll just raise.
                if self._allow_existing_model and "already exists" in (e.stderr or ""):
                    pass
                else:
                    raise

        self._models[model_name] = juju
        return juju

    def _dump_all_logs(self, path: Path = Path(DEFAULT_JDL_DUMP_PATH)):
        path.mkdir(parents=True, exist_ok=True)
        for model, juju in self._models.items():
            jdl_path = path / (model + JDL_LOGFILE_EXTENSION)
            jdl = juju.cli("debug-log", "--replay")
            jdl_path.write_text(jdl)
            logging.info(f"dropping jdl for model {model} to {jdl_path}")

    def _teardown(self, force: bool = False):
        for model, juju in self._models.items():
            juju.destroy_model(model, destroy_storage=True, force=force)


@pytest.fixture(scope="module")
def temp_model_factory(request):
    user_model = request.config.getoption("--model")
    if user_model:
        prefix = user_model
        randbits = None
    else:
        prefix = (request.module.__name__.rpartition(".")[-1]).replace("_", "-")
        randbits = secrets.token_hex(4)
    factory = TempModelFactory(
        prefix=prefix,
        randbits=randbits,
        allow_existing_model=user_model,
        add_model=not request.config.getoption("--no-setup"),
    )

    yield factory

    # BEFORE tearing down the models, dump any and all juju debug-logs
    if dump_logs := request.config.getoption("--dump-logs"):
        factory._dump_all_logs(Path(dump_logs))

    if not request.config.getoption("--no-teardown"):
        # TODO: jubilant defaults to --force, but is that a good idea?
        factory._teardown(force=True)


@pytest.fixture(scope="module")
def juju(request, temp_model_factory):
    juju = temp_model_factory.get_juju("")
    if request.config.getoption("--switch"):
        juju.cli("switch", juju.model, include_model=False)
    return juju


@dataclasses.dataclass
class _Result:
    charm: Path
    resources: dict[str, str] | None


def _pack(root: Path | str, platform: str | None = None):
    platform_ = f" --platform {platform}" if platform else ""
    cmd = f"charmcraft pack -p {root}{platform_}"
    proc = subprocess.run(
        shlex.split(cmd),
        check=True,
        capture_output=True,
        text=True,
    )

    # The output looks like:
    # ❯ charmcraft pack
    # Packed tempo-coordinator-k8s_ubuntu@24.04-amd64.charm
    # Packed tempo-coordinator-k8s_ubuntu@22.04-amd64.charm

    # Don't ask me why this goes to stderr.
    output = proc.stderr

    # we parse it and collect all the built charms.
    packed_charms = [
        line.split()[1] for line in output.strip().splitlines() if line.startswith("Packed")
    ]

    if not packed_charms:
        raise ValueError(
            f"unable to get packed charm(s) ({cmd!r} completed with {proc.returncode=}, {proc.stdout=}, {proc.stderr=})"
        )

    return packed_charms


def pack(root: Path | str = "./", platform: str | None = None) -> Path:
    """Pack a local charm and return it."""
    packed_charms = _pack(root, platform)

    if len(packed_charms) > 1:
        raise ValueError(
            "This charm supports multiple platforms. "
            "Pass a `platform` argument to control which charm you're getting instead."
        )

    return Path(packed_charms[0]).resolve()


def get_resources(root: Path | str = "./") -> dict[str, str] | None:
    """Obtain the charm resources from metadata.yaml's upstream-source fields."""
    for meta_name in ("metadata.yaml", "charmcraft.yaml"):
        if (meta_yaml := Path(root) / meta_name).exists():
            logging.debug(f"found metadata file: {meta_yaml}")
            meta = yaml.safe_load(meta_yaml.read_text())
            if meta_resources := meta.get("resources"):
                try:
                    resources = {
                        resource: res_meta["upstream-source"]
                        for resource, res_meta in meta_resources.items()
                    }
                except KeyError:
                    logging.exception(
                        "The `upstream-source` key wasn't found in the resource. If your charm follows a different convention of pointing at an OCI image, you need to pack it manually."
                    )
                    raise
            else:
                resources = None
                logging.info(f"resources not found in {meta_name}; proceeding without resources")
            break
    else:
        resources = None
        logging.error(f"metadata/charmcraft.yaml not found at {root}; unable to load resources")

    return resources
