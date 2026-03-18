import pathlib

pytest_plugins = ["pytester"]

TEST_PASS = (pathlib.Path(__file__).parent / "lifecycle_tests.py").read_text()


def test_no_dump_logs(pytester):
    pytester.makepyfile(test_file=TEST_PASS)

    result = pytester.runpytest()

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    assert not (pytester.path / ".logs").exists()


def test_dump_logs_default_path(pytester):
    pytester.makepyfile(test_file=TEST_PASS)

    result = pytester.runpytest("--model", "modelt", "--dump-logs")

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    foo_log_path = pytester.path / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = pytester.path / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makepyfile(test_file=TEST_PASS)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--model", "modelt", "--dump-logs", str(custom_dir))

    outcomes = result.parseoutcomes()
    print(outcomes)
    assert outcomes.get("passed")
    assert not outcomes.get("failed")
    assert not outcomes.get("errors")
    assert not outcomes.get("warnings")

    foo_log_path = custom_dir / ".logs" / "modelt-foo-jdl.txt"
    assert foo_log_path.exists()
    bar_log_path = custom_dir / ".logs" / "modelt-bar-jdl.txt"
    assert bar_log_path.exists()
