from unittest.mock import call

from pytest_jubilant._main import _juju_arch


def test_rootmodel(cli_mock, juju):
    juju.deploy("something")

    assert cli_mock.called
    assert cli_mock.call_args_list == [
        call(
            ["juju", "add-model", "--no-switch", "jubilant-deadbeef-test-rootmodel"],
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
                "jubilant-deadbeef-test-rootmodel",
                f"arch={_juju_arch()}",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
        call(
            ["juju", "deploy", "--model", "jubilant-deadbeef-test-rootmodel", "something"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]
