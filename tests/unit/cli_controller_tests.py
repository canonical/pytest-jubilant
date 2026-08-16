"""This file is executed via test_cli_controller.py, it should not be run directly."""

from unittest.mock import MagicMock, call

import pytest_jubilant
from pytest_jubilant._main import _juju_arch


def test_model_is_prefixed_with_controller(
    cli_mock: MagicMock,
    juju_factory: pytest_jubilant.JujuFactory,
):
    """If ``--juju-controller`` is set, it is used as the model prefix in ``juju add-model``."""
    cli_mock.reset_mock()
    juju = juju_factory.get_juju("my-model")
    assert juju.model == "my-fancy-controller:jubilant-deadbeef-test-file-my-model"
    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                "jubilant-deadbeef-test-file-my-model",
                "--controller",
                "my-fancy-controller",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
        call(
            [
                "juju",
                "set-model-constraints",
                "--model",
                "my-fancy-controller:jubilant-deadbeef-test-file-my-model",
                f"arch={_juju_arch()}",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]


def test_get_juju_overrides_controller(
    cli_mock: MagicMock,
    juju_factory: pytest_jubilant.JujuFactory,
):
    """If JujuFactory is called with a controller argument, it should override the CLI argument."""
    cli_mock.reset_mock()
    juju = juju_factory.get_juju("override-model", controller="override-controller")
    assert juju.model == "override-controller:jubilant-deadbeef-test-file-override-model"
    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                "jubilant-deadbeef-test-file-override-model",
                "--controller",
                "override-controller",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
        call(
            [
                "juju",
                "set-model-constraints",
                "--model",
                "override-controller:jubilant-deadbeef-test-file-override-model",
                f"arch={_juju_arch()}",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]
