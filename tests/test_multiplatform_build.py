import contextlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pytest_jubilant import pack


@contextlib.contextmanager
def mock_charmcraft_subprocess_call(packed_charms):
    new = MagicMock()
    new.return_value.stderr = "\n".join([f"Packed {charm}" for charm in packed_charms])
    new.return_value.stdout = ""
    new.return_value.returncode = 0
    with patch("subprocess.run", new) as mock:
        yield mock


def test_pack_build_failure():
    with mock_charmcraft_subprocess_call([]):
        with pytest.raises(ValueError, match="unable to get packed charm\(s\).*"):
            pack("./")


def test_pack_single_platform():
    with mock_charmcraft_subprocess_call(["tempo.charm"]):
        assert pack("./") == Path("tempo.charm")


def test_pack_multiplatform_unspecified():
    with mock_charmcraft_subprocess_call(["tempo-amd64.charm", "tempo-arm64.charm"]):
        with pytest.raises(
            ValueError, match="This charm supports multiple platforms\..*"
        ):
            pack("./")
