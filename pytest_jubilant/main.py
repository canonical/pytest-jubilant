#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""
import dataclasses
import logging
import os
import secrets
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Union, Optional, Dict
from unittest.mock import MagicMock, patch

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
        help="Switch to the temporary model that is currently being worked on.",
    )
    group.addoption(
        "--force",
        action="store_true",
        default=True, # this is jubilant's default!
        help="Use force when tearing down temp models.",
    )
    group.addoption(
        "--dump-logs",
        action="store",
        default=DEFAULT_JDL_DUMP_PATH,
        help="Directory in which to dump any juju debug-log for any model prior to tearing it down. "
        "Set to empty string to disable the behaviour.",
    )


_cli_mock: Optional[MagicMock] = None


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "setup: tests that setup some parts of the environment."
    )
    config.addinivalue_line(
        "markers", "teardown: tests that tear down some parts of the environment."
    )

    # horrible to do it this way, but it's easy
    if os.getenv("PYTESTING_PYTEST_JUBILANT"):
        mm = MagicMock()
        mm.return_value = MagicMock(stdout="output", stderr="error")
        ctx = patch("subprocess.run", new=mm)
        ctx.__enter__()
        global _cli_mock
        _cli_mock = mm


def pytest_collection_modifyitems(config: pytest.Config, items):
    def _set_keep_models(val: bool = True):
        # TODO: less hacky way to do this?
        optname = config._opt2dest.get("--keep-models", "--keep-models")  # noqa
        config.option.__setattr__(optname, val)

    if config.getoption("--no-teardown"):
        skipper = pytest.mark.skip(reason="--no-teardown provided.")
        for item in items:
            if "teardown" in item.keywords:
                item.add_marker(skipper)

        if config.getoption("--keep-models"):
            logging.warning("--no-teardown implies --keep-models")
        else:
            _set_keep_models(True)

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
        randbits: Optional[str] = None,
        check_models_unique: bool = True,
            switch:bool=False
    ):
        self.prefix = prefix
        self.switch = switch
        self.randbits = randbits
        self._models: Dict[str, jubilant.Juju] = {}
        self._check_models_unique = check_models_unique

    def get_temp_model(self, suffix: str) -> jubilant.Juju:
        model_name = "-".join(filter(None, (self.prefix, self.randbits, suffix)))
        if model_name in self._models:
            raise ValueError(
                f"model {model_name} already registered on this temp_model factory. "
                "choose a different prefix."
            )

        temp_model = jubilant.Juju(model=model_name)
        try:
            temp_model.add_model(model_name)
            if self.switch:
                temp_model.cli("switch", model_name)
        except jubilant.CLIError as e:
            # If --model is set (_check_models_unique is False), then the user wants collisions.
            # If the name is randomly generated, the chance of colliding with another
            # randomly generated model that wasn't torn down is tiny, but still present.
            if (
                "already exists on this k8s cluster" in e.args[1]
                and self._check_models_unique
            ):
                raise

        self._models[model_name] = temp_model
        return temp_model

    def dump_all_logs(self, path: Path = Path(DEFAULT_JDL_DUMP_PATH)):
        path.mkdir(parents=True, exist_ok=True)
        for model, temp_model in self._models.items():
            jdl_path = path / (model + JDL_LOGFILE_EXTENSION)
            jdl = temp_model.cli("debug-log", "--replay")
            jdl_path.write_text(jdl)
            logging.info(f"dropping jdl for model {model} to {jdl_path}")

    def teardown(self, force: bool = False):
        for model, temp_model in self._models.items():
            temp_model.destroy_model(model, destroy_storage=True, force=force)


@pytest.fixture(scope="module")
def cli_mock(request):
    if not os.getenv("PYTESTING_PYTEST_JUBILANT"):
        raise RuntimeError("cannot access this fixture at this time")
    yield _cli_mock


@pytest.fixture(scope="module", autouse=True)
def patch_jubilant(temp_model_factory, request):
    import jubilant
    @contextmanager
    def _temp_model(keep: bool=None):
        if keep is not None:
            logging.warning("keep arg to temp_model ignored: this setting is managed by "
                            "pytest-jubilant's --keep-models pytest config flag.")
        suffix = (request.module.__name__.rpartition(".")[-1]).replace("_", "-")
        tm = temp_model_factory.get_temp_model(suffix)
        yield tm

    orig_add_model = jubilant.Juju.add_model
    def _add_model(*args, **kwargs):
        logging.warning("caution: models obtained directly via Juju.add_model won't be managed by pytest-jubilant.")
        return orig_add_model(*args, **kwargs)

    with patch.object(jubilant.Juju, "add_model", _add_model):
        with patch.object(jubilant, "temp_model", _temp_model):
            yield


def _temp_model_generator(
    model_name:Optional[str]=None,
    dump_logs: Optional[Path]=None,
    keep_models: bool=False,
    switch: bool=False,
    force: bool=False,
    prefix:str="jubilant-"
      ):
    """Yield a temp model."""
    if model_name:
        prefix = model_name
        randbits = None
    else:
        randbits = (
            "testing"
            if os.getenv("PYTESTING_PYTEST_JUBILANT")
            else secrets.token_hex(4)
        )
    factory = TempModelFactory(
        prefix=prefix, randbits=randbits, check_models_unique=not model_name, switch=switch
    )

    yield factory

    # BEFORE tearing down the models, dump any and all juju debug-logs
    if dump_logs:
        factory.dump_all_logs(Path(dump_logs))

    if not keep_models:
        factory.teardown(force=force)

    if _cli_mock:
        _cli_mock.reset_mock()


@pytest.fixture(scope="module")
def temp_model_factory(request):
    yield from _temp_model_generator(
        model_name = request.config.getoption("--model"),
        dump_logs = Path(request.config.getoption("--dump-logs")),
        prefix=(request.module.__name__.rpartition(".")[-1]).replace("_", "-"),
        keep_models=request.config.getoption("--keep-models"),
        force = request.config.getoption("--force"),
        switch = request.config.getoption("--switch")
    )


@pytest.fixture(scope="module")
def temp_model(request, temp_model_factory):
    temp_model = temp_model_factory.get_temp_model("")
    return temp_model


@pytest.fixture(scope="module")
def juju(temp_model):
    logging.warning(
        "the 'juju' fixture is deprecated and will be removed in v2.0. "
        "Use `temp_model` going forward."
        )
    yield temp_model


@dataclasses.dataclass
class _Result:
    charm: Path
    resources: Optional[Dict[str, str]]


def _pack(root: Union[Path, str], platform: Optional[str] = None):
    _platform = f" --platform {platform}" if platform else ""
    cmd = f"charmcraft pack -p {root}{_platform}"
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
    packed_charms = []
    for line in output.strip().splitlines():
        if line.startswith("Packed"):
            packed_charms.append(line.split()[1])

    if not packed_charms:
        raise ValueError(
            f"unable to get packed charm(s) ({cmd!r} completed with {proc.returncode=}, {proc.stdout=}, {proc.stderr=})"
        )

    return packed_charms


def pack(root: Union[Path, str] = "./", platform: Optional[str] = None) -> Path:
    """Pack a local charm and return it."""
    packed_charms = _pack(root, platform)

    if len(packed_charms) > 1:
        raise ValueError(
            "This charm supports multiple platforms. "
            "Pass a `platform` argument to control which charm you're getting instead."
        )

    return Path(packed_charms[0]).resolve()


def get_resources(root: Union[Path, str] = "./") -> Optional[Dict[str, str]]:
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
                logging.info(
                    f"resources not found in {meta_name}; proceeding without resources"
                )
            break
    else:
        resources = None
        logging.error(
            f"metadata/charmcraft.yaml not found at {root}; unable to load resources"
        )

    return resources
