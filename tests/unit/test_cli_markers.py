from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = (Path(__file__).parent / "cli_markers_tests.py").read_text()


def test_default(pytester: pytest.Pytester):
    """By default, all tests are run, and models are created and torn down."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest()

    result.assert_outcomes(passed=3)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
        "jubilant-deadbeef-test-file-regular",
        "jubilant-deadbeef-test-file-teardown",
    ]
    # Teardown occurs in the same order as they were registered.
    assert (pytester.path / "destroyed.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
        "jubilant-deadbeef-test-file-regular",
        "jubilant-deadbeef-test-file-teardown",
    ]


def test_no_setup_ok(pytester: pytest.Pytester):
    """``--no-setup`` means tests marked ``setup`` aren't run, and models aren't created.

    This is only permitted if ``--model`` is also passed.
    We'll tear down the models unless ``--no-teardown`` is also passed.
    """
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-setup", "--juju-model", "model-t")

    result.assert_outcomes(passed=2, skipped=1)
    assert not (pytester.path / "added.txt").exists()
    assert (pytester.path / "destroyed.txt").read_text().splitlines() == [
        "model-t-test-file-autouse-module-scoped-fixture",
        "model-t-test-file-regular",
        "model-t-test-file-teardown",
    ]


def test_no_setup_without_model_is_an_error(pytester: pytest.Pytester):
    """It's an immediate error to pass ``--no-setup`` without also pasing ``--model``."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-setup")

    assert result.ret == 4  # Exit code for a pytest.UsageError
    result.stderr.re_match_lines([
        ".*--no-juju-setup cannot be specified without --juju-model.*",
        ".*unless you specify --no-juju-teardown, the model.*",
    ])


def test_no_teardown(pytester: pytest.Pytester):
    """``--no-teardown`` means tests marked ``teardown`` aren't run, and models aren't torn down"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-teardown")

    result.assert_outcomes(passed=2, skipped=1)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
        "jubilant-deadbeef-test-file-regular",
    ]
    assert not (pytester.path / "destroyed.txt").exists()


def test_no_setup_and_no_teardown_ok(pytester: pytest.Pytester):
    """``--no-setup`` and ``--no-teardown`` both being passed means neither are run.

    This only works if ``--model`` is specified.
    """
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-setup", "--no-juju-teardown", "--juju-model", "model-t")

    result.assert_outcomes(passed=1, skipped=2)
    assert not (pytester.path / "added.txt").exists()
    assert not (pytester.path / "destroyed.txt").exists()


def test_no_setup_and_no_teardown_without_model_is_an_error(pytester: pytest.Pytester):
    """``--no-setup`` and ``--no-teardown`` both being passed without ``--model`` is an error."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--no-juju-setup", "--no-juju-teardown")

    assert result.ret == 4  # Exit code for a pytest.UsageError
    result.stderr.re_match_lines([".*--no-juju-setup cannot be specified without --juju-model.*"])


def test_m_setup(pytester: pytest.Pytester):
    """``-m setup`` only runs tests marked ``setup``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("-m", "juju_setup")

    result.assert_outcomes(passed=1, deselected=2)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
    ]
    assert (pytester.path / "destroyed.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
    ]


def test_m_setup_with_no_teardown(pytester: pytest.Pytester):
    """``-m setup`` + ``--no-teardown`` means only ``setup`` tests run + models aren't torn down"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("-m", "juju_setup", "--no-juju-teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
    ]
    assert not (pytester.path / "destroyed.txt").exists()


def test_m_teardown(pytester: pytest.Pytester):
    """``-m teardown`` only runs tests marked ``teardown``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("-m", "juju_teardown")

    result.assert_outcomes(passed=1, deselected=2)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-teardown",
    ]
    assert (pytester.path / "destroyed.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-teardown",
    ]


def test_keep_models_is_unknown(pytester: pytest.Pytester):
    """``pytest-jubilant`` doesn't define ``--keep-models``"""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--keep-models")

    assert result.ret != 0
    assert any("--keep-models" in line for line in result.errlines)


def test_keep_models_is_ignored(pytester: pytest.Pytester):
    """If a user defines ``--keep-models``, we don't respect it."""
    keep_models_conftest = f"""
{CONFTEST}


def pytest_addoption(parser):
    parser.addoption("--keep-models", action="store_true", default=False)
""".strip()
    pytester.makeconftest(keep_models_conftest)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--keep-models")

    result.assert_outcomes(passed=3)
    assert (pytester.path / "added.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
        "jubilant-deadbeef-test-file-regular",
        "jubilant-deadbeef-test-file-teardown",
    ]
    assert (pytester.path / "destroyed.txt").read_text().splitlines() == [
        "jubilant-deadbeef-test-file-autouse-module-scoped-fixture",
        "jubilant-deadbeef-test-file-setup",
        "jubilant-deadbeef-test-file-regular",
        "jubilant-deadbeef-test-file-teardown",
    ]
