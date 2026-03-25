"""Type checking statements for library internals -- not executed."""

# pyright: reportPrivateUsage=false

import pytest_jubilant
import pytest_jubilant._main


def needs_temp_model_factory(_: pytest_jubilant.TempModelFactory): ...


def implements_temp_model_factory(t: pytest_jubilant._main._TempModelFactory):
    needs_temp_model_factory(t)
