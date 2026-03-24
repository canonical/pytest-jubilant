import pathlib

import jubilant


def test_smoke(smoke_charm: pathlib.Path, juju: jubilant.Juju):
    juju.deploy(smoke_charm)
    juju.wait(jubilant.all_active, timeout=60 * 30)
