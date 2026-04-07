"""Type checking statements for library internals -- not executed."""

# pyright: reportPrivateUsage=false

import pytest_jubilant
import pytest_jubilant._main


def needs_juju_factory(_: pytest_jubilant.JujuFactory): ...


def implements_juju_factory(t: pytest_jubilant._main._JujuFactory):
    needs_juju_factory(t)
