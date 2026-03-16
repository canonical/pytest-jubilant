from pathlib import Path

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST = """
def test_use_factory(temp_model_factory):
    temp_model_factory.get_juju("foo")
""".strip()


def test_dump_logs_not_passed(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)

    assert not (pytester.path / ".logs").exists()


def test_dump_logs_default_path(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST)

    result = pytester.runpytest("--dump-logs")
    result.assert_outcomes(passed=1)

    log_path = pytester.path / ".logs" / "test-sample-testing-foo-jdl.txt"
    assert log_path.exists()
    assert log_path.read_text() == "output"


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--dump-logs", str(custom_dir))
    result.assert_outcomes(passed=1)

    log_path = custom_dir / "test-sample-testing-foo-jdl.txt"
    assert log_path.exists()
    assert log_path.read_text() == "output"
