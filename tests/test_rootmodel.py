from unittest.mock import call


def test_rootmodel(temp_model, cli_mock):
    temp_model.deploy("something")

    assert cli_mock.called
    assert cli_mock.call_args_list == [
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
