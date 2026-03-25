from unittest.mock import call


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
        ),
        call(
            ["juju", "deploy", "--model", "jubilant-deadbeef-test-rootmodel", "something"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
    ]
