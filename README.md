# Pytest plugin for jubilant.

Eases the transition from pytest-operator to jubilant.
And some cool stuff on top.

# Fixtures

## `juju`
This is a module(and model!)-scoped fixture that, by default, uses a temporary model and tears it down on context exit.

See also the `--model`, `--no-setup`, and `--no-teardown` options below, which modify its behavior.

> [!TIP]
> Use `jubilant.Juju` as the type annotation for the `juju` fixture in your tests for better linting and IDE autocompletions.

Usage:

```python
# test_smoke.py
"""Test that the charm can be deployed and go to active status."""

import jubilant


def test_deploy(juju: jubilant.Juju):
    juju.deploy("./foo.charm", "foo")
    juju.wait(lambda status: jubilant.all_active(status, "foo"), timeout=1000)
```

This test will spin up a temporary model named `jubilant-<randomhex>-test-smoke`.


## `temp_model_factory`
This is a module-scoped fixture that manages temporary models for your test runs.
It is what the `juju` fixture is using behind the scenes.

Especially useful if you have test cases that require multiple models.

> [!TIP]
> Use `pytest_jubilant.TempModelFactory` as the type annotation for the `temp_model_factory` fixture in your tests for better linting and IDE autocompletions.
>
> Note that the exposed `TempModelFactory` type is just a protocol, and can't be used to directly create a temp model factory. Request the `temp_model_factory` fixture instead.

Usage:

```python
# test_cmr.py
"""Test cross model relations."""

import jubilant
import pytest
import pytest_jubilant


@pytest.fixture(scope="module")
def istio(temp_model_factory: pytest_jubilant.TempModelFactory):
    yield temp_model_factory.get_juju(suffix="istio")


def test_offer_consume_relate(juju: jubilant.Juju, istio: jubilant.Juju):
    istio.deploy("istio-k8s", "istio")
    istio.wait(lambda status: all_active(status, "istio"), timeout=1000)

    juju.deploy("./foo.charm", "foo")
    juju.wait(lambda status: jubilant.all_active(status, "foo"), timeout=1000)

    juju.cli("offer", "foo:bar")
    istio.cli("consume", f"{juju.model}:foo")
    istio.cli("relate", "istio", "foo:bar")
```

This test will spin up two temporary models, one called `jubilant-<randomhex>-test-cmr`, and one called `jubilant-<randomhex>-test-cmr-istio`, and tear them down on context exit.

`pytest tests/integration --model my-prefix` will use `my-prefix` instead of `jubilant-<randomhex>`. The module names combined with the suffixes you defined in the fixtures will give all generated models predictable names. The tests will reuse the existing models (if found) or create new ones with those names.


# Pytest CLI options

## `--model`
By default, created Juju model names are prefixed with `jubilant-<randomhex>`, where `<randomhex>` is randomly generated each `pytest` run.
Set `--model` on the commandline to use a fixed prefix instead.
Do note that models created with this prefix **will** be torn down at the end of the test run just like any other, so if you're targeting existing models you care about, don't forget the `--no-teardown` flag!.

Usage example, assuming a single model per module:

    pytest tests/integration/test_foo.py::test_something --model my-prefix
    # runs the test on new 'my-prefix-test-foo' model and tears it down afterwards

    juju add-model my-prefix-test-foo
    pytest tests/integration/test_foo.py::test_something --model my-prefix --no-teardown
    # runs the tests on the existing 'my-prefix-test-foo' model and keeps it
    # note that we want to run the setup tests to deploy the charm(s) etc

    pytest tests/integration/test_foo.py::test_something --model my-prefix --no-setup --no-teardown
    # runs the tests on an existing 'my-prefix-test-foo' model, skipping setup tests, and keeps it
    # we might run this after the previous example which ran setup tests and didn't tear down


## `--switch`
Switch to the (possibly randomly-named) model that is currently in scope, so you can keep an
eye on the juju status as the tests progress.
(Won't work well if you're running multiple test modules in parallel.)
Only switches to models created by the `juju` fixture, not those created by `temp_model_factory`.

Usage:

    pytest ./tests/integration -k test_something --switch
    # will switch you to the 'jubilant-<randomhex>-<module>' model as soon as it's created

    pytest ./tests/integration -k test_something --model my-prefix --switch
    # will switch you to the 'my-prefix-<module>' model as soon as it's created


## `--no-teardown`
Skip all tests marked with `teardown` and skip destroying the models.
Useful to inspect the state of a model after a (failed) test run.

> [!WARNING]
> The `--keep-models` flag used by `pytest-operator` is unsupported as of `pytest-jubilant` 2.0!
> Be sure to use `--no-teardown` instead.

Usage:
    pytest ./tests/integration --no-teardown


## `--no-setup`
Skip all tests marked with `setup`. Especially useful when re-running a test on an existing model which is already set-up, but not torn down.
See [this article](https://discourse.charmhub.io/t/14006) for the idea behind this workflow.
Usage:

    pytest ./tests/integration --no-teardown # make a note of the temporary model name
    pytest ./tests/integration --model <temporary model prefix> --no-setup


## `--dump-logs`
Prior to tearing down all models owned by a temp_model_factory (i.e. prior to cleaning up a test module execution), dump the `juju debug-log --replay` for each model into a directory (default `"<CWD>/.logs"`). File naming scheme is:

`<module name>-<random bits>[-<suffix>]-jdl.txt`

Usage:

    pytest ./tests/integration ./integration/test_ingress.py --dump-logs=./debug_logs
    # once the tests are done, you'll find the logs in
    # ./debug_logs/test-ingress-c372ef49-jdl.txt (random bits may vary).

    pytest ./tests/integration ./integration/test_ingress.py --model foo --dump-logs=./debug_logs
    # once the tests are done, you'll find the logs in
    # ./debug_logs/foo-test-ingress-juju-debug.log

    pytest ./tests/integration ./integration/test_ingress.py --dump-logs=""
    # no logs will be saved


# Markers

## `setup`

Marker for tests that prepare (parts of) a model.

Usage:

```python
import pytest


@pytest.mark.setup
def test_deploy(juju):
    juju.deploy("A")
    juju.deploy("B")


@pytest.mark.setup
def test_relate(juju):
    juju.integrate("A", "B")
```


## `teardown`
Marker for tests that destroy (parts of) a model.

Usage:

```python
import pytest


@pytest.mark.teardown
def test_disintegrate(juju):
    juju.remove_relation("A", "B")


@pytest.mark.teardown
def test_destroy(juju):
    juju.remove_application("A")
    juju.remove_application("B")
```

# DEVELOPERS

To release:
```bash
# obtain the current latest version out there
git tag | tail -n 1

new_tag="v0.5"  # for example!
git tag $new_tag -m "new fancy feature"
git push origin head --tag
```

Once the PR is merged, the release CI will kick in and put the tag in `pytest_jubilant/_version.py`
