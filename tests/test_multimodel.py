from unittest.mock import call

import pytest


@pytest.fixture(scope="module")
def istio(temp_model_factory):
    yield temp_model_factory.get_juju(suffix="istio")


@pytest.fixture(scope="module")
def tempo(temp_model_factory):
    yield temp_model_factory.get_juju(suffix="tempo")


def test_multimodel(juju, istio, tempo, cli_mock):
    assert istio.model == juju.model + "-istio"
    assert tempo.model == juju.model + "-tempo"

    juju.deploy("something")
    istio.deploy("somethingelse")

    assert cli_mock.called
    assert cli_mock.call_args_list == [
        call(
            ["juju", "add-model", "--no-switch", "test-multimodel-testing"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "add-model", "--no-switch", "test-multimodel-testing-istio"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "add-model", "--no-switch", "test-multimodel-testing-tempo"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "deploy", "--model", "test-multimodel-testing", "something"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            [
                "juju",
                "deploy",
                "--model",
                "test-multimodel-testing-istio",
                "somethingelse",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
    ]
