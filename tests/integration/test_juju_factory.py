import pathlib

import jubilant
import pytest

import pytest_jubilant


@pytest.fixture(scope="module")
def juju_one(juju_factory: pytest_jubilant.JujuFactory):
    """Juju instance for a model on the machine model."""
    yield juju_factory.get_juju(suffix="one")


@pytest.fixture(scope="module")
def juju_two(juju_factory: pytest_jubilant.JujuFactory, juju_controller: str):
    """Juju instance for a model on the machine model with specified controller."""
    yield juju_factory.get_juju(suffix="two", controller=juju_controller)


def test_juju_factory_deploy_charm(
    smoke_charm: pathlib.Path,
    juju_one: jubilant.Juju,
    juju_controller: str,
):
    """Test application is properly deployed when using JujuFactory."""
    juju_one.deploy(smoke_charm)
    juju_one.wait(jubilant.all_active, timeout=60 * 30)

    # Given we didn't specify a controller, the model name should not be prefixed
    assert juju_one.model is not None and not juju_one.model.startswith(f"{juju_controller}:")


def test_juju_factory_prefix_controller_in_model(
    smoke_charm: pathlib.Path,
    juju_two: jubilant.Juju,
    juju_controller: str,
):
    """Test model name is correctly prefixed with controller when using JujuFactory."""
    juju_two.deploy(smoke_charm)
    juju_two.wait(jubilant.all_active, timeout=60 * 30)

    # Given we specified a controller, the model name should be prefixed with it
    assert juju_two.model is not None and juju_two.model.startswith(f"{juju_controller}:")
