import pytest


@pytest.fixture
def istio(temp_model_factory):
    yield temp_model_factory.get_juju(suffix="istio")


@pytest.fixture
def tempo(temp_model_factory):
    yield temp_model_factory.get_juju(suffix="tempo")


def test_foo(juju, istio, tempo):
    print(juju.model, istio.model, tempo.model)
