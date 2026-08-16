#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Main plugin module."""

from __future__ import annotations

import logging
import pathlib
import platform
import secrets
import time
import typing

import jubilant
import pytest

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from _pytest.terminal import TerminalReporter

logger = logging.getLogger("pytest-jubilant")

# If the test failure occurs in the middle of a Juju operation, like processing an action,
# then the logs for the operation in question might not be fully processed by Juju yet.
# Testing with a mid-action failure several hundred times, 2 seconds seems like a reliable
# enough amount of time to wait and always have the logs (though in practice this will depend
# on factors like system load). Several hundred tests with a 1 second wait had a handful of
# cases where the logs were missing the latest lines.
_LOG_WAIT = 2.0  # Time to wait before processing logs if we need them.

# Unique per-session key to stash the model prefix for later output.
_MODEL_PREFIX_KEY = pytest.StashKey[str]()

# Map Python's platform.machine() names to the architecture names Juju uses.
# Anything not listed is passed through unchanged, since names like amd64, arm64,
# s390x, and riscv64 already match. Compare concierge's goArchToJujuArch.
_MACHINE_TO_JUJU_ARCH = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
    "ppc64le": "ppc64el",
}


def _juju_arch() -> str:
    """Return the Juju architecture name for the current runtime."""
    machine = platform.machine().lower()
    return _MACHINE_TO_JUJU_ARCH.get(machine, machine)


def pytest_addoption(parser: pytest.Parser):
    """Register the ``--juju-*`` command-line options under the "jubilant" group.

    Pytest hook: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_addoption
    """
    group = parser.getgroup("jubilant")
    group.addoption(
        "--juju-model",
        action="store",
        default=None,
        help="Prefix for Juju model names.",
    )
    group.addoption(
        "--juju-controller",
        action="store",
        default=None,
        help="The default Juju controller to use for tests.",
    )
    group.addoption(
        "--juju-cloud",
        action="store",
        default=None,
        help="The default Juju cloud to use for tests.",
    )
    group.addoption(
        "--no-juju-setup",
        action="store_true",
        default=False,
        help='Skip tests marked with "juju_setup".',
    )
    group.addoption(
        "--no-juju-teardown",
        action="store_true",
        default=False,
        help='Skip tests marked with "juju_teardown".',
    )
    group.addoption(
        "--juju-switch",
        action="store_true",
        default=False,
        help="Switch to the temporary model that is currently being worked on.",
    )
    group.addoption(
        "--juju-dump-logs",
        action="store",
        nargs="?",
        const=pathlib.Path(".logs"),
        default=None,
        type=pathlib.Path,
        help="Dump the juju debug-log for each model prior to teardown. "
        "The default dump location is './.logs'.",
    )


def pytest_configure(config: pytest.Config):
    """Register the ``juju_setup`` and ``juju_teardown`` markers, and validate option combinations.

    Pytest hook: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_configure
    """
    config.addinivalue_line(
        "markers", "juju_setup: tests that setup some parts of the environment."
    )
    config.addinivalue_line(
        "markers", "juju_teardown: tests that tear down some parts of the environment."
    )
    if config.getoption("--no-juju-setup") and not config.getoption("--juju-model"):
        msg = (
            "--no-juju-setup cannot be specified without --juju-model"
            ", because --no-juju-setup will skip model creation"
            ", and surely your tests need a model."
        )
        if not config.getoption("--no-juju-teardown"):
            msg += (
                "\nNote that unless you specify --no-juju-teardown"
                ", the model(s) identified by --juju-model *will* be torn down!"
            )
        raise pytest.UsageError(msg)


def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: pytest.ExitCode,
    config: pytest.Config,
):
    """Print a usage hint after the test summary."""
    prefix = config.stash.get(_MODEL_PREFIX_KEY, default=None)
    if prefix is None:  # nothing that used juju_factory ran
        return
    terminalreporter.write_sep("-", "jubilant")
    if config.getoption("--no-juju-teardown"):
        terminalreporter.write_line(
            "Models were not torn down. To rerun tests on these models"
            " and skip setup tests and model teardown, pass the following:"
        )
        terminalreporter.write_line(f"--no-juju-setup --no-juju-teardown --juju-model {prefix}")
    else:
        terminalreporter.write_line(
            "Models were torn down. To keep models available for subsequent"
            " test runs or manual debugging, pass the following:"
        )
        terminalreporter.write_line("--no-juju-teardown")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """Skip ``juju_setup``/``juju_teardown`` tests when the matching ``--no-juju-*`` flag is set.

    Pytest hook: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_collection_modifyitems
    """
    if config.getoption("--no-juju-teardown"):
        skipper = pytest.mark.skip(reason="--no-juju-teardown provided.")
        for item in items:
            if "juju_teardown" in item.keywords:
                item.add_marker(skipper)

    if config.getoption("--no-juju-setup"):
        skipper = pytest.mark.skip(reason="--no-juju-setup provided.")
        for item in items:
            if "juju_setup" in item.keywords:
                item.add_marker(skipper)


class JujuFactory(typing.Protocol):
    """Protocol for a factory of per-test temporary Juju models.

    Used as a type annotation for fixtures yielding the concrete
    factory (see the ``juju_factory`` fixture).
    """

    def get_juju(
        self,
        suffix: str,
        *,
        controller: str | None = None,
        cloud: str | None = None,
    ) -> jubilant.Juju:
        """Return a `jubilant.Juju` for a model named `<prefix>-<suffix>`.

        `<prefix>` is the factory's configured model-name prefix. If `suffix`
        is empty, the model is named `<prefix>`. The same factory cannot
        return two `Juju` instances for the same model name; raises
        `ValueError` if called twice with the same `suffix`.

        Pass `controller` and/or `cloud` to override the default Juju controller
        and cloud on a per-model basis. These default to the values passed
        on the command line (`--juju-controller`/`--juju-cloud`), with Juju falling
        back to the active controller and cloud if they're not specified.
        """
        ...


class _JujuFactory:
    """Manages temporary models for testing."""

    def __init__(
        self,
        model_prefix: str,
        allow_existing_model: bool = False,
        log_path: pathlib.Path | None = None,
        add_model: bool = False,
        controller: str | None = None,
        cloud: str | None = None,
    ):
        self._model_prefix = model_prefix
        self._models: dict[str, jubilant.Juju] = {}
        self._allow_existing_model = allow_existing_model
        self._log_path = log_path
        self._add_model = add_model
        self._controller = controller
        self._cloud = cloud

    def get_juju(
        self,
        suffix: str,
        *,
        controller: str | None = None,
        cloud: str | None = None,
    ) -> jubilant.Juju:
        # Set controller and cloud for add_model, preferring args to factory defaults
        juju_controller = controller if controller is not None else self._controller
        juju_cloud = cloud if cloud is not None else self._cloud

        short_model_name = f"{self._model_prefix}-{suffix}" if suffix else self._model_prefix

        # Include the controller prefix in the model_name for subsequent Juju calls.
        model_name = (
            f"{juju_controller}:{short_model_name}" if juju_controller else short_model_name
        )
        if model_name in self._models:
            raise ValueError(
                f"model {model_name} already registered on this juju_factory. "
                "choose a different prefix."
            )
        juju = jubilant.Juju(model=model_name)
        if self._add_model:
            created = True
            try:
                # juju add-model does not support the <controller>:<model> syntax
                juju.add_model(
                    model=short_model_name, cloud=juju_cloud, controller=juju_controller
                )
            except jubilant.CLIError as e:
                # If --model is set (_allow_existing_model is True), then the user wants collisions.
                # If the name is randomly generated, the chance of colliding with another
                # randomly generated model that wasn't torn down is tiny, so we we'll just raise.
                if self._allow_existing_model and "already exists" in (e.stderr or ""):
                    created = False
                else:
                    raise

            # Match the model architecture to the runtime. When a cloud is explicitly chosen
            # we are less confident about its architecture, so leave it alone.
            if created and juju_cloud is None:
                arch = _juju_arch()
                juju.model_constraints({"arch": arch})

        self._models[model_name] = juju
        return juju

    def _dump_all_logs(self):
        if not self._log_path:
            return

        self._log_path.mkdir(parents=True, exist_ok=True)
        for model, juju in self._models.items():
            jdl = juju.debug_log()
            model_filename = model.replace(":", "-")
            jdl_path = self._log_path / (model_filename + "-juju-debug.log")
            jdl_path.write_text(jdl)
            logger.info("Wrote full `juju debug-log` for model %s to %s", model, jdl_path)

    def _teardown(self, force: bool = False):
        for model, juju in self._models.items():
            juju.destroy_model(model, destroy_storage=True, force=force)


@pytest.fixture(scope="session")
def _model_prefix(request: pytest.FixtureRequest) -> str:  # pyright: ignore[reportUnusedFunction]
    """Generate a prefix for the session or use the user-provided one."""
    user_prefix = typing.cast("str | None", request.config.getoption("--juju-model"))
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
def juju_factory(
    request: pytest.FixtureRequest,
    _sleep_once: Callable[[], None],
    _model_prefix: str,
):
    """Module-scoped factory for creating one or more temporary Juju models.

    Use this when a test module needs more than one model. For the common
    single-model case, use the `juju` fixture instead. Models created via this
    factory are torn down at module teardown unless `--no-juju-teardown` is set.
    """
    module_name = typing.cast("str", request.module.__name__)  # type: ignore
    module_part = module_name.rpartition(".")[-1].replace("_", "-")
    dump_logs = typing.cast("pathlib.Path | None", request.config.getoption("--juju-dump-logs"))
    controller_name = typing.cast("str | None", request.config.getoption("--juju-controller"))
    cloud_name = typing.cast("str | None", request.config.getoption("--juju-cloud"))
    factory = _JujuFactory(
        model_prefix=f"{_model_prefix}-{module_part}",
        allow_existing_model=bool(request.config.getoption("--juju-model")),
        log_path=dump_logs,
        add_model=not typing.cast("bool", request.config.getoption("--no-juju-setup")),
        controller=controller_name,
        cloud=cloud_name,
    )

    yield factory

    # BEFORE tearing down the models, dump any and all juju debug-logs
    if dump_logs:
        _sleep_once()  # Wait for Juju to process logs or the latest lines might be missing
    factory._dump_all_logs()  # pyright: ignore[reportPrivateUsage]

    if not request.config.getoption("--no-juju-teardown"):
        # Match jubilant's temp_model fixture: --force so failed tests with apps
        # in error states don't hang teardown.
        factory._teardown(force=True)  # pyright: ignore[reportPrivateUsage]


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest, juju_factory: JujuFactory):
    """Module-scoped temporary Juju model.

    Returns a `jubilant.Juju` bound to a freshly created model that lives for
    the duration of the test module. Pass `--juju-switch` to make this the
    active model in your local `juju` CLI while the tests run.
    """
    juju = juju_factory.get_juju("")
    if request.config.getoption("--juju-switch"):
        assert juju.model  # noqa: S101
        juju.cli("switch", juju.model, include_model=False)
    return juju
