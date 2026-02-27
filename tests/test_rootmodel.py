from unittest.mock import call


def test_rootmodel(cli_mock_module, juju):
    juju.deploy("something")

    assert cli_mock_module.called
    assert cli_mock_module.call_args_list == [
        call(
            ["juju", "add-model", "--no-switch", "test-rootmodel-testing"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "deploy", "--model", "test-rootmodel-testing", "something"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
    ]
