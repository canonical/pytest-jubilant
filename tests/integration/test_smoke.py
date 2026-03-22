import pathlib

import jubilant


def test_smoke(juju: jubilant.Juju, simple_charm: pathlib.Path):
    juju.deploy(simple_charm)
    juju.wait(jubilant.all_active, timeout=600)
