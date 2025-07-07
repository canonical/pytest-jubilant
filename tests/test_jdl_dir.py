from pathlib import Path
from shutil import rmtree

from pytest_jubilant.main import DEFAULT_JDL_DUMP_PATH


def test_jdl_dir(temp_model_factory):
    if Path(DEFAULT_JDL_DUMP_PATH).exists():
        rmtree(DEFAULT_JDL_DUMP_PATH)

    # create two models
    temp_model_factory.get_juju("foo")
    temp_model_factory.get_juju("bar")

    # trigger an early log-dump for all models
    temp_model_factory.dump_all_logs()

    for model in ("foo", "bar"):
        expected_path = (
            Path(DEFAULT_JDL_DUMP_PATH) / f"test-jdl-dir-testing-{model}-jdl.txt"
        )
        assert expected_path.exists(), f"{expected_path.absolute()} not found"
        assert expected_path.read_text() == "output"
