from pathlib import Path

pytest_plugins = ["pytester"]

CONFTEST = (Path(__file__).parent / "conftest.py").read_text()
TEST_FILE = """
def test_use_factory(juju_factory):
    juju_factory.get_juju("foo")
    juju_factory.get_juju("bar")
""".strip()


def test_dump_logs_not_passed(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)

    assert not (pytester.path / ".logs").exists()


def test_dump_logs_empty_path_disables(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-dump-logs", "")
    result.assert_outcomes(passed=1)

    assert not list(pytester.path.rglob("*-juju-debug.log"))


def test_dump_logs_default_path(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-dump-logs")
    result.assert_outcomes(passed=1)

    foo_log_path = pytester.path / ".logs" / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert foo_log_path.read_text() == "stdout patched by conftest.py"
    bar_log_path = pytester.path / ".logs" / "jubilant-deadbeef-test-file-bar-juju-debug.log"
    assert bar_log_path.exists()
    assert bar_log_path.read_text() == "stdout patched by conftest.py"


def test_dump_logs_default_path_uses_log_file_directory(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    log_file = tmp_path / "pytest-logs" / "pytest.log"

    result = pytester.runpytest("--juju-dump-logs", "--log-file", str(log_file))
    result.assert_outcomes(passed=1)

    foo_log_path = log_file.parent / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert not (pytester.path / ".logs").exists()


def test_dump_logs_default_path_uses_ini_log_file_directory(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    pytester.makeini("[pytest]\nlog_file = ci-logs/pytest.log\n")

    result = pytester.runpytest("--juju-dump-logs")
    result.assert_outcomes(passed=1)

    foo_log_path = pytester.path / "ci-logs" / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert not (pytester.path / ".logs").exists()


def test_dump_logs_default_path_ignores_log_file_without_directory(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    pytester.makeini("[pytest]\nlog_file = pytest.log\n")

    result = pytester.runpytest("--juju-dump-logs")
    result.assert_outcomes(passed=1)

    foo_log_path = pytester.path / ".logs" / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert not list(pytester.path.glob("*-juju-debug.log"))


def test_dump_logs_default_path_without_logging_plugin(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("-p", "no:logging", "--juju-dump-logs")
    result.assert_outcomes(passed=1)

    foo_log_path = pytester.path / ".logs" / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()


def test_dump_logs_default_path_ignores_log_file_when_given_explicit_path(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    log_file = tmp_path / "pytest-logs" / "pytest.log"
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--juju-dump-logs", str(custom_dir), "--log-file", str(log_file))
    result.assert_outcomes(passed=1)

    foo_log_path = custom_dir / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert not (log_file.parent / "jubilant-deadbeef-test-file-foo-juju-debug.log").exists()


def test_dump_logs_custom_path(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_file=TEST_FILE)
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest("--juju-dump-logs", str(custom_dir))
    result.assert_outcomes(passed=1)

    foo_log_path = custom_dir / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
    assert foo_log_path.read_text() == "stdout patched by conftest.py"
    bar_log_path = custom_dir / "jubilant-deadbeef-test-file-bar-juju-debug.log"
    assert bar_log_path.exists()
    assert bar_log_path.read_text() == "stdout patched by conftest.py"


CHDIR_FIXTURE = """

@pytest.fixture(scope="session", autouse=True)
def _chdir_elsewhere(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path_factory.mktemp("elsewhere"))
    try:
        yield
    finally:
        mp.undo()
"""


def test_dump_logs_relative_path_resolved_before_chdir(pytester):
    pytester.makeconftest(CONFTEST + CHDIR_FIXTURE)
    pytester.makepyfile(test_file=TEST_FILE)

    result = pytester.runpytest("--juju-dump-logs", "relative-logs")
    result.assert_outcomes(passed=1)

    foo_log_path = (
        pytester.path / "relative-logs" / "jubilant-deadbeef-test-file-foo-juju-debug.log"
    )
    assert foo_log_path.exists()


def test_juju_debug_log_on_failure(pytester, tmp_path):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(
        test_file="""
def test_fail(juju_factory):
    juju_factory.get_juju("foo")
    assert False
"""
    )
    custom_dir = tmp_path / "custom-logs"

    result = pytester.runpytest_subprocess(
        "--juju-model", "model-t", "--juju-dump-logs", str(custom_dir)
    )

    # We expect this session to fail.
    result.assert_outcomes(failed=1)

    # The full logs are still written on failure with --dump-logs.
    foo_log_path = custom_dir / "model-t-test-file-foo-juju-debug.log"
    assert foo_log_path.exists()
