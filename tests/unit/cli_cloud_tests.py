"""This file is executed via test_cli_cloud.py, it should not be run directly."""

from unittest.mock import MagicMock, call

import pytest_jubilant


def test_cloud_is_passed_to_add_model(
    cli_mock: MagicMock,
    juju_factory: pytest_jubilant.JujuFactory,
):
    """If ``--juju-cloud`` is set, it is passed to ``juju add-model`` as a positional argument.

    A cloud may run a different architecture, so no ``arch`` constraint is set in this case.
    """
    cli_mock.reset_mock()
    juju_factory.get_juju("my-model")
    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                "jubilant-deadbeef-test-file-my-model",
                "my-fancy-cloud",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]


def test_get_juju_overrides_cloud(
    cli_mock: MagicMock,
    juju_factory: pytest_jubilant.JujuFactory,
):
    """If JujuFactory is called with a cloud argument, it should override the CLI argument.

    Passing a cloud (here or via ``--juju-cloud``) also suppresses the ``arch`` constraint.
    """
    cli_mock.reset_mock()
    juju_factory.get_juju("override-model", cloud="override-cloud")
    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                "jubilant-deadbeef-test-file-override-model",
                "override-cloud",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]
