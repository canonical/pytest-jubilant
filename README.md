# The Canonical pytest plugin for Jubilant

`pytest-jubilant` is a [pytest](https://docs.pytest.org) plugin for [Jubilant](https://documentation.ubuntu.com/jubilant/).

Jubilant is a Python library that wraps the [Juju](https://canonical.com/juju) CLI, primarily for use in [charm](https://canonical.com/juju/charms-architecture) integration tests. `pytest-jubilant` provides additional pytest-specific functionality on top of Jubilant.

> Read more: [pytest-jubilant's design goals](./CONTRIBUTING.md#design-goals)


## Getting started

`pytest-jubilant`'s features are available to use as long as it's installed in the Python environment where you're invoking `pytest`. The best way to ensure this is to add both `pytest` and `pytest-jubilant` to your dependencies like this.
```toml
# pyproject.toml
[dependency-groups]
integration = [
    "pytest>=9,<10",
    "pytest-jubilant>=2,<3",
]
```
And ensure that the `integration` dependency group is installed when running your integration tests, for example with:
```shell
uv run --group integration pytest tests/integration
```

Get started writing your own Jubilant integration tests with [the how-to guide in the Ops docs](https://documentation.ubuntu.com/ops/latest/howto/write-integration-tests-for-a-charm/).


Read on for an explanation of the [fixtures](#fixtures), [CLI options](#cli-options), and [markers](#markers) provided by `pytest-jubilant`.


## Fixtures

`pytest-jubilant`'s fixtures are available as long as `pytest-jubilant` is installed. You can [request a fixture](https://docs.pytest.org/en/stable/how-to/fixtures.html) by declaring it as an argument for the test that needs it.


### `juju`

This is a module-scoped fixture that creates a temporary Juju model and tears it down when the tests in the module have finished.

You can use combinations of the [--juju-model](#--juju-model), [--no-juju-setup](#--no-juju-setup), and [--no-juju-teardown](#--no-juju-teardown) options to reuse models across multiple integration test runs.

> [!TIP]
> Use `jubilant.Juju` as the type annotation for the `juju` fixture in your tests for better linting and IDE autocompletions.

**Usage:**

```python
# test_smoke.py
"""Test that the charm can be deployed and go to active status."""

import jubilant


def test_deploy(juju: jubilant.Juju):
    juju.deploy("./foo.charm", "foo")
    juju.wait(lambda status: jubilant.all_active(status, "foo"), timeout=1000)
```

This test will spin up a temporary model named `jubilant-<randomhex>-test-smoke`. It will be torn down when the module-scoped `juju` fixture context exits.


### `juju_factory`

This is a module-scoped fixture that you can use to manage multiple temporary Juju models. It's what the `juju` fixture is using behind the scenes. It's useful if you have test cases that require multiple models, for example testing cross-model relations.

> [!TIP]
> Use `pytest_jubilant.JujuFactory` as the type annotation for the `juju_factory` fixture in your tests for better linting and IDE autocompletions.
>
> Note that the exposed `JujuFactory` type is just a protocol, and can't be used to directly create a Juju factory. Whenever you need one, request the `juju_factory` fixture.

**Usage:**

```python
# test_cmr.py
"""Test cross model relations."""

import jubilant
import pytest
import pytest_jubilant


@pytest.fixture(scope="module")
def istio(juju_factory: pytest_jubilant.JujuFactory):
    yield juju_factory.get_juju(suffix="istio")


def test_offer_consume_relate(juju: jubilant.Juju, istio: jubilant.Juju):
    istio.deploy("istio-k8s", "istio")
    istio.wait(lambda status: all_active(status, "istio"), timeout=1000)

    juju.deploy("./foo.charm", "foo")
    juju.wait(lambda status: jubilant.all_active(status, "foo"), timeout=1000)

    juju.cli("offer", "foo:bar")
    istio.cli("consume", f"{juju.model}:foo")
    istio.cli("relate", "istio", "foo:bar")
```

This test will spin up two temporary models, one called `jubilant-<randomhex>-test-cmr`, and one called `jubilant-<randomhex>-test-cmr-istio`. They'll be torn down when the module context exits.

`pytest tests/integration --juju-model hello` will use `hello` instead of `jubilant-<randomhex>`. The module names combined with the suffixes you defined in the fixtures will give all generated models predictable names. The tests will reuse the existing models (if found) or create new ones with those names.

You can optionally pass `controller` and `cloud` to `juju_factory.get_juju` to deploy individual models on specific controllers or clouds. This is useful for testing cross-model relations between different deployment types, such as machine and Kubernetes models on separate controllers.


## CLI options

`pytest-jubilant` extends `pytest` with several commandline arguments that you can add directly to your `pytest` invocation.

### `--no-juju-setup`

Skip all tests marked with `juju_setup` and don't create any new models. This option is for re-running a test on an existing model which is already set up. Since setup can be very lengthy, it's often helpful to avoid re-running it when iterating on tests that assume the charm is up and running, for example when testing actions.

> [!WARNING]
> It's an error to pass `--no-juju-setup` without also specifying `--juju-model`.

**Usage:**

```shell
pytest tests/integration --no-juju-teardown
# Check the last line of output for the <model prefix>!
pytest tests/integration --no-juju-setup --juju-model <model prefix>
```


### `--no-juju-teardown`

Skip all tests marked with `juju_teardown` and skip destroying the models.
Useful to inspect the state of a model after a (failed) test run.

> [!WARNING]
> The `--keep-models` flag used by `pytest-operator` is unsupported as of `pytest-jubilant` 2.0!
> Be sure to use `--no-juju-teardown` instead.

**Usage:**

```shell
pytest tests/integration --no-juju-teardown
```

> [!TIP]
> The last line of output will tell you the `--juju-model` value to use if you want to rerun your tests using the same models. Be sure to pass `--no-juju-setup` as well to avoid failures when trying to perform setup steps that are already done.


### `--juju-model`

By default, created Juju model names are prefixed with `jubilant-<randomhex>`, where `<randomhex>` is randomly generated each `pytest` run. Set `--juju-model` on the commandline to use a fixed prefix instead.

> [!WARNING]
> Note that models created with this prefix **will** be torn down at the end of the test run just like any other, so if you're targeting existing models you care about, don't forget the `--no-juju-teardown` flag!

**Usage:**

```shell
pytest tests/integration/test_foo.py --juju-model hello
# Runs the test on new 'hello-test-foo' model and tears it down afterwards.

pytest tests/integration/test_foo.py --juju-model hello --no-juju-teardown
# Runs the test on new 'hello-test-foo' model and keeps it.

pytest tests/integration/test_foo.py --juju-model hello --no-juju-setup --no-juju-teardown
# Runs the test on the existing 'hello-test-foo' model and keeps it.
# Note that we don't want to run the setup tests since they already ran.
```
```shell
juju add-model hello-test-bar  # A whole new model.
pytest tests/integration/test_bar.py --juju-model hello --no-juju-teardown
# Runs the test on the existing 'hello-test-bar' model and keeps it.
# Note that we want to run the setup tests to deploy the charm(s) etc.
# since this is a new model.
```


### `--juju-controller`

Set the default Juju controller to use when creating new models. This is equivalent to passing `--controller` to `juju add-model`. It can be overridden by passing the `controller` argument to `JujuFactory.get_juju`. If neither is specified, Juju falls back to the currently active controller.

**Usage:**

```shell
pytest tests/integration --juju-controller my-controller
```


### `--juju-cloud`

Set the default Juju cloud (or cloud/region) to use when creating new models. This is equivalent to passing the cloud argument to `juju add-model`. It can be overridden by passing the `cloud` argument to `JujuFactory.get_juju`. If neither is specified, Juju falls back to the currently active cloud.

**Usage:**

```shell
pytest tests/integration --juju-cloud localhost
pytest tests/integration --juju-cloud aws/us-east-1
```


### `--juju-switch`

Switch to the model that is currently in scope, so you can keep an eye on the juju status as the tests progress. This won't be very helpful if you're running multiple test modules in parallel!

Only switches to models created by the `juju` fixture, not those created by `juju_factory`.

**Usage:**

```shell
pytest tests/integration -k test_something --juju-switch
# will switch you to the 'jubilant-<randomhex>-<module>' model as soon as it's created

pytest tests/integration -k test_something --juju-model hello --juju-switch
# will switch you to the 'hello-<module>' model as soon as it's created
```


### `--juju-dump-logs`

When all the tests in a module have completed, but prior to tearing down the models owned by a [juju_factory](#juju_factory), dump the `juju debug-log` for each managed model into the specified directory.

- By default, logs aren't dumped, and `juju debug-log` is only executed if tests failed, so that the last log lines can be sent to stderr.
- If `--juju-dump-logs` is passed, logs are dumped to `<CWD>/.logs/`.
- If `--juju-dump-logs <target dir>` is passed, logs are dumped to `<target dir>/`.

The file naming scheme is:
```
<module prefix>-<module name>[-<suffix>]-juju-debug.log
```

**Usage:**

```shell
pytest tests/integration/test_ingress.py --juju-dump-logs=debug_logs
# Once the tests are done, you'll find the logs in:
# ./debug_logs/jubilant-abcd1234-test-ingress-juju-debug.log

pytest tests/integration/test_ingress.py --juju-model foo --juju-dump-logs
# Once the tests are done, you'll find the logs in the default directory:
# ./.logs/foo-test-ingress-juju-debug.log

pytest integration/test_ingress.py
# No logs will be saved.
```

> [!TIP]
> Use `--juju-dump-logs` in combination with [actions/upload-artifact](https://github.com/actions/upload-artifact) to make your logs available in CI.
>
> For example:
> ```yaml
>   # In your integration test job
>   - run: tox -e integration -- --juju-dump-logs logs
>   - name: Upload logs
>     if: ${{ !cancelled() }}
>     uses: actions/upload-artifact@v4
>     with:
>       name: juju-dump-logs
>       path: logs
> ```
> Note that dumping to the default location `.logs/` will require you to set `include-hidden-files: true`.


## Markers

`pytest-jubilant` declares markers that you can apply to your tests with `@pytest.mark.<marker>`.

### `juju_setup`

Marker for tests that prepare a model for use in later tests.

The [--no-juju-setup](#--no-juju-setup) option will skip any tests marked with `juju_setup`, in addition to not destroying the Juju models themselves.

> [!TIP]
> To run only your `juju_setup` tests and leave the models set up for manual interaction, try:
>
> ```
> pytest tests/integration -m juju_setup --no-juju-teardown
> ```

**Usage:**

```python
import jubilant
import pytest


@pytest.mark.juju_setup
def test_deploy(juju: jubilant.Juju):
    juju.deploy("A")
    juju.deploy("B")


@pytest.mark.juju_setup
def test_relate(juju: jubilant.Juju):
    juju.integrate("A", "B")
```


### `juju_teardown`

Marker for tests that perform destructive actions on a model.

The [--no-juju-teardown](#--no-juju-teardown) option will skip any tests marked with `juju_teardown`, in addition to not destroying the Juju models themselves.

**Usage:**

```python
import jubilant
import pytest


@pytest.mark.juju_teardown
def test_disintegrate(juju: jubilant.Juju):
    juju.remove_relation("A", "B")


@pytest.mark.juju_teardown
def test_destroy(juju: jubilant.Juju):
    juju.remove_application("A")
    juju.remove_application("B")
```

## Project and community

`pytest-jubilant` is an open source project that warmly welcomes community contributions, suggestions, fixes and constructive feedback.

- [Report a bug](https://github.com/canonical/pytest-jubilant/issues)
- [Contribute](./CONTRIBUTING.md)
- [Code of conduct](./CODE_OF_CONDUCT.md)

For support, join [Charm Development](https://matrix.to/#/#charmhub-charmdev:ubuntu.com) on Matrix.

To follow along with updates and tips about charm development, join our [Discourse forum](https://discourse.charmhub.io/).
