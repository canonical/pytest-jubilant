from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_ALREADY_EXISTS = (Path(__file__).parent / "cli_model_tests_already_exists.py").read_text()
TEST_OTHER_CLI_ERROR = (Path(__file__).parent / "cli_model_tests_other_cli_error.py").read_text()


def test_explicit_model_allows_collisions(pytester: pytest.Pytester):
    """If ``--prefix`` is set, an existing model error is allowed (and expected)."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_ALREADY_EXISTS)

    result = pytester.runpytest("--prefix", "my-fancy-model")

    result.assert_outcomes(passed=1)


def test_collision_without_explicit_model_raises(pytester: pytest.Pytester):
    """Without ``--prefix``, an existing model error is raised if there's a collision."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_ALREADY_EXISTS)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    module_name = "test-file"
    session_id = "deadbeef"
    suffix = "my-fancy-model"
    model_name = f"jubilant-{session_id}-{module_name}-{suffix}"
    msg = (
        "ERROR failed to create new model: "
        f'model "{model_name}" for admin already exists (already exists)'
    )
    assert msg in result.stdout.str()


def test_explicit_model_doesnt_prevent_other_errors(pytester: pytest.Pytester):
    """If ``--prefix`` is set, an existing model error is allowed (and expected)."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_OTHER_CLI_ERROR)

    result = pytester.runpytest("--prefix", "my-fancy-model")

    result.assert_outcomes(failed=1)
    assert "ERROR something else" in result.stdout.str()


def test_other_error_without_explicit_model_raises(pytester: pytest.Pytester):
    """Without ``--prefix``, an existing model error is raised if there's a collision."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_OTHER_CLI_ERROR)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    assert "ERROR something else" in result.stdout.str()
