# Pytest plugin for jubilant.

Eases the transition from pytest-operator to jubilant.
And some cool stuff on top.

# Fixtures

## `juju` 
This is a model-scoped fixture that uses a temporary model and tears it down on context exit.
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


# Pytest CLI options

## `--model`
Target a specific, existing model instead of provisioning a fresh, temporary one.
Do note that this model won't be torn down at the end of the test run.
Usage:

> juju add-model mymodel
> pytest ./tests/integration -k test_foo --model "mymodel"  

## `--switch`
Switch to the (randomly-named) model that is currently in scope, so you can keep an 
eye on the juju status as the tests progress. 
(Won't work well if you're running multiple test modules in parallel.)

> pytest ./tests/integration --switch

## `--keep-models`
Skip destroying the newly generated models when the tests are done. 
Usage:

> pytest ./tests/integration --keep-models  


## `--no-teardown`
Skip all tests marked with `teardown`. Useful to inspect the state of a model after a (failed) test run.
Implies `--keep-models`.

> pytest ./tests/integration --no-teardown 


## `--no-setup`
Skip all tests marked with `setup`. Especially useful when re-running a test on an existing model which is already set-up, but not torn down.
See [this article](https://discourse.charmhub.io/t/14006) for the idea behind this workflow.
Usage:

> pytest ./tests/integration --no-teardown # make a note of the temporary model name
> pytest ./tests/integration --model <temporary model name> --no-setup 


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

## `pack_charm`

Wrapper around `charmcraft pack` to build a charm and return the packed charm path and its resources, ready to be passed to `juju.deploy`.

```python
from pytest_jubilant import pack_charm
import pytest

@pytest.mark.setup
def test_build_deploy_charm(juju):
    out = pack_charm("/path/to/foo-charm-repo-root-dir/")
    juju.deploy(
        out.charm,
        "foo",
        # the resources can only be inferred from the charm's metadata/charmcraft yaml 
        # if you use the `upstream-source` convention
        resources=out.resources,
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