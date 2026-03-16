from pathlib import Path

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()

TEST_MARKERS = """
import pytest


@pytest.mark.setup
def test_setup():
    assert True


@pytest.mark.teardown
def test_teardown():
    assert True


def test_regular():
    assert True
""".strip()


TEST_KEEP_MODELS = """
from pathlib import Path

import pytest
import jubilant

DESTROY_LOG = Path("{tmp_file}")


@pytest.fixture(scope="session", autouse=True)
def _patch_destroy_model():
    mp = pytest.MonkeyPatch()

    def _destroy(self, model, destroy_storage=True, force=False):
        DESTROY_LOG.write_text(model)

    mp.setattr(jubilant.Juju, "destroy_model", _destroy)
    yield
    mp.undo()


def test_keep_models_option_ignored(temp_model_factory):
    temp_model_factory.get_juju("foo")
""".strip()


def test_no_teardown_skips_teardown_markers(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("--no-teardown")

    result.assert_outcomes(passed=2, skipped=1)


def test_no_setup_skips_setup_markers(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("--no-setup")

    result.assert_outcomes(passed=2, skipped=1)


def test_no_setup_and_no_teardown_skips_both_markers(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("--no-setup", "--no-teardown")

    result.assert_outcomes(passed=1, skipped=2)


def test_marker_selection_setup_only(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "setup")

    result.assert_outcomes(passed=1, deselected=2)


def test_marker_selection_teardown_only(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "teardown")

    result.assert_outcomes(passed=1, deselected=2)


def test_marker_setup_with_no_setup(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "setup", "--no-setup")

    result.assert_outcomes(skipped=1, deselected=2)


def test_marker_setup_with_no_teardown(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "setup", "--no-teardown")

    result.assert_outcomes(passed=1, deselected=2)


def test_marker_teardown_with_no_teardown(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "teardown", "--no-teardown")

    result.assert_outcomes(skipped=1, deselected=2)


def test_marker_teardown_with_no_setup(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST_MARKERS)

    result = pytester.runpytest("-m", "teardown", "--no-setup")

    result.assert_outcomes(passed=1, deselected=2)


def test_keep_models_option_is_unknown(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample="def test_ok(): assert True")

    result = pytester.runpytest("--keep-models")

    assert result.ret != 0
    assert any("--keep-models" in line for line in result.errlines)


def test_keep_models_option_is_ignored(pytester, tmp_path):
    keep_models_conftest = CONFTEST + """

def pytest_addoption(parser):
    parser.addoption("--keep-models", action="store_true", default=False)
"""
    destroy_log = tmp_path / "destroyed.txt"
    test_sample = TEST_KEEP_MODELS.format(tmp_file=destroy_log.as_posix())

    pytester.makeconftest(keep_models_conftest)
    pytester.makepyfile(test_sample=test_sample)

    result = pytester.runpytest("--keep-models")

    result.assert_outcomes(passed=1)
    assert destroy_log.exists()
    assert destroy_log.read_text() == "test-sample-testing-foo"
