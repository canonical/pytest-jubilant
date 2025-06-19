# Pytest plugin for jubilant.

Eases the transition from pytest-operator to jubilant.
And some cool stuff on top.

# Fixtures

## `juju` 
This is a module(and model!)-scoped fixture that, by default, uses a temporary model and tears it down on context exit.
Cfr. the `--model`, `--keep-models`, and `--no-teardown` options below for more.
Usage:

```python
from jubilant import Juju, all_active

def test_deploy(juju: Juju):
    juju.deploy("./foo.charm", "foo")
    juju.wait(
        lambda status: all_active(status, "foo"),
        timeout=1000
    )
```

## `temp_model_factory`
This is a module-scoped fixture that manages temporary models for your test runs. 
It is what the `juju` fixture is using behind the scenes. 

Especially useful if you have test cases that require multiple models.
```python
import pytest
from jubilant import Juju, all_active

@pytest.fixture
def istio(temp_model_factory):
    yield temp_model_factory.get_juju(suffix="istio")
    
    
def test_cmr(juju: Juju, istio: Juju):
    istio.deploy("istio-k8s", "istio")
    istio.wait(
        lambda status: all_active(status, "istio"),
        timeout=1000
    )

    juju.deploy("./foo.charm", "foo")
    juju.wait(
        lambda status: all_active(status, "foo"),
        timeout=1000
    )

    juju.cli("offer", "foo:bar") 
    istio.cli("consume", f"{juju.model}:foo")
    istio.cli("relate", "istio", "foo:bar")
```

This test will spin up two temporary models, one called `test-cmr-<randomhex>`, and one called `test-cmr-<randomhex>istio`, 
and tear them down on context exit.

This fixture can be used with the options described below:
- `pytest tests/test_cmr.py --keep-models` will skip model teardown for all generated models.
- `pytest tests/test_cmr.py --model test-cmr-<randomhex>` will use `test-cmr-<randomhex>` as base name, and the suffixes you defined in the fixtures will give all generated models predictable names, which means that the tests will reuse the existing models (if found) or create new ones with those names.
- `pytest tests/test_cmr.py --switch` will switch you to the 'base' model `test-cmr-<randomhex>` (not to one of the suffixed ones!).


# Pytest CLI options

## `--model`
Target a specific, existing model instead of provisioning a fresh, temporary one.
Do note that this model won't be torn down at the end of the test run.
Usage:

    juju add-model mymodel
    pytest ./tests/integration -k test_foo --model "mymodel"  

## `--switch`
Switch to the (randomly-named) model that is currently in scope, so you can keep an 
eye on the juju status as the tests progress. 
(Won't work well if you're running multiple test modules in parallel.)

    pytest ./tests/integration --switch

## `--keep-models`
Skip destroying the newly generated models when the tests are done. 
Usage:

    pytest ./tests/integration --keep-models  


## `--no-teardown`
Skip all tests marked with `teardown`. Useful to inspect the state of a model after a (failed) test run.

    pytest ./tests/integration --no-teardown 


## `--no-setup`
Skip all tests marked with `setup`. Especially useful when re-running a test on an existing model which is already set-up, but not torn down.
See [this article](https://discourse.charmhub.io/t/14006) for the idea behind this workflow.
Usage:

    pytest ./tests/integration --no-teardown # make a note of the temporary model name
    pytest ./tests/integration --model <temporary model name> --no-setup 


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

# Utilities

## `pack`

Wrapper around `charmcraft pack` to build a charm and return the packed charm path and its resources, ready to be passed to `juju.deploy`.

```python
from pytest_jubilant import pack, get_resources
import pytest


@pytest.mark.setup
def test_build_deploy_charm(juju):
    charm_root = "/path/to/foo-charm-repo-root-dir/"
    juju.deploy(
        pack(charm_root),
        "foo",
        # the resources can only be inferred from the charm's metadata/charmcraft yaml 
        # if you use the `upstream-source` convention
        resources=get_resources(charm_root),
        num_units=3,
    )
```


```yaml
# example /path/to/foo-charm-repo-root-dir/charmcraft.yaml

# [snip] 
resources:
  nginx-image:
    type: oci-image
    description: OCI image for nginx
    upstream-source: ubuntu/nginx:1.24-24.04_beta
  nginx-prometheus-exporter-image:
    type: oci-image
    description: OCI image for nginx-prometheus-exporter
    upstream-source: nginx/nginx-prometheus-exporter:1.1.0
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

Once the PR is merged, the release CI will kick in and put the tag in `pytest_jubilant.version.py`