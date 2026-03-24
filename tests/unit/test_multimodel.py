from unittest.mock import MagicMock, call

import jubilant
import pytest

import pytest_jubilant


@pytest.fixture(scope="module")
def istio(temp_model_factory: pytest_jubilant.TempModelFactory):
    yield temp_model_factory.get_juju(suffix="istio")


@pytest.fixture(scope="module")
def tempo(temp_model_factory: pytest_jubilant.TempModelFactory):
    yield temp_model_factory.get_juju(suffix="tempo")


def test_multimodel(cli_mock: MagicMock, juju: jubilant.Juju, istio: jubilant.Juju, tempo: jubilant.Juju):
    assert juju.model is not None
    assert istio.model == juju.model + "-istio"
    assert tempo.model == juju.model + "-tempo"

    juju.deploy("something")
    istio.deploy("somethingelse")

    assert cli_mock.called
    assert cli_mock.call_args_list == [
        call(
            ["juju", "add-model", "--no-switch", "jubilant-deadbeef-test-multimodel"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "add-model", "--no-switch", "jubilant-deadbeef-test-multimodel-istio"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "add-model", "--no-switch", "jubilant-deadbeef-test-multimodel-tempo"],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
        call(
            ["juju", "deploy", "--model", "jubilant-deadbeef-test-multimodel", "something"],
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
                "jubilant-deadbeef-test-multimodel-istio",
                "somethingelse",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
        ),
    ]
