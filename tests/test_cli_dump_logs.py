from pathlib import Path

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST = """
def test_use_factory(temp_model_factory):
    temp_model_factory.get_juju("foo")
    temp_model_factory.get_juju("bar")
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

    foo_log_path = pytester.path / ".logs" / "test-sample-testing-foo-jdl.txt"
    assert foo_log_path.exists()
    assert foo_log_path.read_text() == "stdout patched by conftest.py"
    bar_log_path = pytester.path / ".logs" / "test-sample-testing-bar-jdl.txt"
    assert bar_log_path.exists()
    assert bar_log_path.read_text() == "stdout patched by conftest.py"


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_sample=TEST)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--dump-logs", str(custom_dir))
    result.assert_outcomes(passed=1)

    foo_log_path = custom_dir / "test-sample-testing-foo-jdl.txt"
    assert foo_log_path.exists()
    assert foo_log_path.read_text() == "stdout patched by conftest.py"
    bar_log_path = custom_dir / "test-sample-testing-bar-jdl.txt"
    assert bar_log_path.exists()
    assert bar_log_path.read_text() == "stdout patched by conftest.py"
