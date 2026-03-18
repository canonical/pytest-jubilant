import pathlib

pytest_plugins = ["pytester"]

TEST_FILE = (pathlib.Path(__file__).parent / "lifecycle_tests.py").read_text()


def test_dump_logs_not_passed(pytester):
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest()

    outcomes = result.parseoutcomes()
    print(outcomes)
    result.assert_outcomes(failed=0, errors=0, warnings=0)

    assert not (pytester.path / ".logs").exists()


def test_dump_logs_default_path(pytester):
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--model", "modelt", "--dump-logs")

    outcomes = result.parseoutcomes()
    print(outcomes)
    result.assert_outcomes(failed=0, errors=0, warnings=0)

    foo_log_path = pytester.path / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = pytester.path / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makepyfile(test_file=TEST_FILE)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "modelt", "--dump-logs", str(custom_dir))

    outcomes = result.parseoutcomes()
    print(outcomes)
    result.assert_outcomes(failed=0, errors=0, warnings=0)

    foo_log_path = custom_dir / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()
