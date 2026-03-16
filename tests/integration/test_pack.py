import pathlib
import secrets
import shutil

import pytest

import pytest_jubilant

FILE = pathlib.Path(__file__)


@pytest.fixture(scope="function")
def local_tmp_path() -> pathlib.Path:
    """Yield the path to a local temporary directory named uniquely for the given test.

    Snaps like Charmcraft can't access /tmp, so we need local temp files.
    """
    tmp_root = FILE.parent / ".tmp"
    tmp_root.mkdir(exist_ok=True)
    tmp_dir = tmp_root / f"{FILE.stem}-{secrets.token_hex(4)}"
    tmp_dir.mkdir()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
    if not list(tmp_root.iterdir()):
        tmp_root.rmdir()


def test_pack_ok(local_tmp_path: pathlib.Path):
    shutil.copytree(FILE.parent / "charms" / "simple", local_tmp_path, dirs_exist_ok=True)
    charm = pytest_jubilant.pack(local_tmp_path)
    assert charm.suffix == ".charm"
