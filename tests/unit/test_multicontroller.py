from unittest.mock import MagicMock, call

import jubilant
import pytest

import pytest_jubilant
from pytest_jubilant._main import _juju_arch

K8S_CONTROLLER = "k8s-controller"
MACHINE_CONTROLLER = "lxd-controller"
MODEL_NAME = "jubilant-deadbeef-test-multicontroller"


@pytest.fixture(scope="module")
def juju_k8s(juju_factory: pytest_jubilant.JujuFactory):
    """Juju instance for a model on the k8s controller."""
    yield juju_factory.get_juju(suffix="k8s", controller=K8S_CONTROLLER)


@pytest.fixture(scope="module")
def juju_machine(juju_factory: pytest_jubilant.JujuFactory):
    """Juju instance for a model on the machine controller."""
    yield juju_factory.get_juju(suffix="machine", controller=MACHINE_CONTROLLER)


def test_multicontroller(
    cli_mock: MagicMock,
    juju_k8s: jubilant.Juju,
    juju_machine: jubilant.Juju,
):
    """Test models on different controllers are correctly prefixed."""

    expected_k8s_model = f"{K8S_CONTROLLER}:{MODEL_NAME}-k8s"
    assert juju_k8s.model == expected_k8s_model

    expected_machine_model = f"{MACHINE_CONTROLLER}:{MODEL_NAME}-machine"
    assert juju_machine.model == expected_machine_model

    juju_k8s.deploy("k8s-charm")
    juju_machine.deploy("machine-charm")

    assert cli_mock.call_args_list == [
        call(
            [
                "juju",
                "add-model",
                "--no-switch",
                f"{MODEL_NAME}-k8s",
                "--controller",
                K8S_CONTROLLER,
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
                f"{K8S_CONTROLLER}:{MODEL_NAME}-k8s",
                f"arch={_juju_arch()}",
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
                "--controller",
                MACHINE_CONTROLLER,
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
                f"{MACHINE_CONTROLLER}:{MODEL_NAME}-machine",
                f"arch={_juju_arch()}",
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
                f"{K8S_CONTROLLER}:{MODEL_NAME}-k8s",
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
                f"{MACHINE_CONTROLLER}:{MODEL_NAME}-machine",
                "machine-charm",
            ],
            check=True,
            capture_output=True,
            encoding="utf-8",
            input=None,
            timeout=None,
        ),
    ]
