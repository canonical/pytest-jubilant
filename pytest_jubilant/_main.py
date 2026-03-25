#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""

from __future__ import annotations

import logging
import pathlib
import secrets
import sys
import time
import typing
from typing import Callable

import jubilant
import pytest

if typing.TYPE_CHECKING:
    from _pytest.terminal import TerminalReporter

# If the test failure occurs in the middle of a Juju operation, like processing an action,
# then the logs for the operation in question might not be fully processed by Juju yet.
# Testing with a mid-action failure several hundred times, 2 seconds seems like a reliable
# enough amount of time to wait and always have the logs (though in practice this will depend
# on factors like system load). Several hundred tests with a 1 second wait had a handful of
# cases where the logs were missing the latest lines.
_LOG_WAIT = 2.0  # Time to wait before processing logs if we need them.
_LOG_LIMIT = 1000  # Number of log lines to dump to stderr on failure.

# Unique per-session key to stash the model prefix for later output.
_MODEL_PREFIX_KEY = pytest.StashKey[str]()


def pytest_addoption(parser: pytest.Parser):
    group = parser.getgroup("jubilant")
    group.addoption(
        "--model",
        action="store",
        default=None,
        help="Prefix for Juju model names.",
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
        const=pathlib.Path(".logs"),
        default=None,
        type=pathlib.Path,
        help="Dump the juju debug-log for each model prior to teardown. "
        "The default dump location is './.logs'.",
    )


def pytest_configure(config: pytest.Config):
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


def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: pytest.ExitCode,
    config: pytest.Config,
):
    """Print a usage hint after the test summary."""
    prefix = config.stash.get(_MODEL_PREFIX_KEY, default=None)
    if prefix is None:  # nothing that used temp_model_factory ran
        return
    terminalreporter.write_sep("-", "jubilant")
    if config.getoption("--no-teardown"):
        terminalreporter.write_line(
            "Models were not torn down. To rerun tests on these models"
            " and skip setup tests and model teardown, pass the following:"
        )
        terminalreporter.write_line(f"--no-setup --no-teardown --model {prefix}")
    else:
        terminalreporter.write_line(
            "Models were torn down. To keep models available for subsequent"
            " test runs or manual debugging, pass the following:"
        )
        terminalreporter.write_line("--no-teardown")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
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


class TempModelFactory(typing.Protocol):
    def get_juju(self, suffix: str) -> jubilant.Juju: ...


class _TempModelFactory:
    """Manages temporary models for testing."""

    def __init__(
        self,
        model_prefix: str,
        allow_existing_model: bool = False,
        log_path: pathlib.Path | None = None,
        add_model: bool = False,
    ):
        self._model_prefix = model_prefix
        self._models: dict[str, jubilant.Juju] = {}
        self._allow_existing_model = allow_existing_model
        self._log_path = log_path
        self._add_model = add_model

    def get_juju(self, suffix: str) -> jubilant.Juju:
        model_name = f"{self._model_prefix}-{suffix}" if suffix else self._model_prefix
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

    def _dump_all_logs(self, *, also_log_lines: int = 0):
        if not (also_log_lines or self._log_path):
            return
        if self._log_path:
            self._log_path.mkdir(parents=True, exist_ok=True)
        for model, juju in self._models.items():
            jdl = juju.debug_log(limit=0 if self._log_path else also_log_lines)
            if also_log_lines:
                msg = f"Logging last {also_log_lines} lines of `juju debug-log` for model {model}:"
                last_n_lines = (
                    "\n".join(jdl.rsplit("\n", also_log_lines)[-also_log_lines:])
                    if self._log_path
                    else jdl
                )
                end_msg = f"--- end of `juju debug-log` for model {model} ---"
                print(f"{msg}\n{last_n_lines}\n{end_msg}", file=sys.stderr, flush=True)
            if self._log_path:
                jdl_path = self._log_path / (model + "-juju-debug.log")
                jdl_path.write_text(jdl)
                logging.info(f"Wrote full `juju debug-log` for model {model} to {jdl_path}")

    def _teardown(self, force: bool = False):
        for model, juju in self._models.items():
            juju.destroy_model(model, destroy_storage=True, force=force)


@pytest.fixture(scope="session")
def _model_prefix(request: pytest.FixtureRequest) -> str:  # pyright: ignore[reportUnusedFunction]
    """Generate a prefix for the session or use the user-provided one."""
    user_prefix = typing.cast("str | None", request.config.getoption("--model"))
    prefix = user_prefix or f"jubilant-{secrets.token_hex(4)}"
    request.config.stash[_MODEL_PREFIX_KEY] = prefix
    return prefix


@pytest.fixture(scope="module")
def _sleep_once():  # pyright: ignore[reportUnusedFunction]
    """Return a function that sleeps when called for the first time.

    The returned function does nothing on repeated calls.
    This allows fixtures of the same scope to ensure a single sleep happens before teardown.
    """
    slept = False

    def sleep():
        nonlocal slept
        if not slept:
            time.sleep(_LOG_WAIT)
            slept = True

    return sleep


@pytest.fixture(scope="module")
def temp_model_factory(
    request: pytest.FixtureRequest,
    _sleep_once: Callable[[], None],
    _model_prefix: str,
):
    module_name = typing.cast("str", request.module.__name__)  # type: ignore
    module_part = module_name.rpartition(".")[-1].replace("_", "-")
    dump_logs = typing.cast("pathlib.Path | None", request.config.getoption("--dump-logs"))
    factory = _TempModelFactory(
        model_prefix=f"{_model_prefix}-{module_part}",
        allow_existing_model=bool(request.config.getoption("--model")),
        log_path=dump_logs,
        add_model=not typing.cast("bool", request.config.getoption("--no-setup")),
    )

    yield factory

    # BEFORE tearing down the models, dump any and all juju debug-logs
    also_log_lines = _LOG_LIMIT if request.session.testsfailed else 0
    if also_log_lines or dump_logs:
        _sleep_once()  # Wait for Juju to process logs or the latest lines might be missing
    factory._dump_all_logs(also_log_lines=also_log_lines)  # pyright: ignore[reportPrivateUsage]

    if not request.config.getoption("--no-teardown"):
        # TODO: jubilant defaults to --force, but is that a good idea?
        factory._teardown(force=True)  # pyright: ignore[reportPrivateUsage]


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest, temp_model_factory: TempModelFactory):
    juju = temp_model_factory.get_juju("")
    if request.config.getoption("--switch"):
        assert juju.model  # noqa: S101
        juju.cli("switch", juju.model, include_model=False)
    return juju
