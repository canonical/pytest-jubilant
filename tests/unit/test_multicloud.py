from unittest.mock import MagicMock, call

import jubilant
import pytest

import pytest_jubilant

K8S_CLOUD = "microk8s"
MACHINE_CLOUD = "localhost"
MODEL_NAME = "jubilant-deadbeef-test-multicloud"


@pytest.fixture(scope="module")
def juju_k8s(juju_factory: pytest_jubilant.JujuFactory):
    """Juju instance for a model on the k8s cloud."""
    yield juju_factory.get_juju(suffix="k8s", cloud=K8S_CLOUD)


@pytest.fixture(scope="module")
def juju_machine(juju_factory: pytest_jubilant.JujuFactory):
    """Juju instance for a model on the machine cloud."""
    yield juju_factory.get_juju(suffix="machine", cloud=MACHINE_CLOUD)


def test_multicloud(
    cli_mock: MagicMock,
    juju_k8s: jubilant.Juju,
    juju_machine: jubilant.Juju,
):
    """Test models on different clouds can be created and deployed to."""

    juju_k8s.deploy("k8s-charm")
    juju_machine.deploy("machine-charm")

    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                f"{MODEL_NAME}-k8s",
                K8S_CLOUD,
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
                "add-model",
                "--no-switch",
                f"{MODEL_NAME}-machine",
                MACHINE_CLOUD,
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
                "deploy",
                "--model",
                f"{MODEL_NAME}-k8s",
                "k8s-charm",
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
                "deploy",
                "--model",
                f"{MODEL_NAME}-machine",
                "machine-charm",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]
