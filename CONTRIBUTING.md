# Contributing

Anyone can contribute to `pytest-jubilant`. It's best to start by [opening an issue](https://github.com/canonical/pytest-jubilant/issues) with a clear description of the problem or feature request, but you can also [open a pull request](https://github.com/canonical/pytest-jubilant/pulls) directly.

Please read about the [design philosophy](#design-philosophy) and [developer tooling](#developing) first.


## Design philosophy

`pytest-jubilant` is downstream of [Jubilant](https://github.com/canonical/jubilant). Where Jubilant is narrowly scoped to interacting with the Juju CLI in a Pythonic way, `pytest-jubilant` aims to provide additional Pytest functionality for Jubilant based integration tests.

`pytest-jubilant` aims to provide a good, opinionated integration testing experience, both in CI, and for local development. Its fixtures will do what they're supposed to anywhere, while the markers and CLI options are designed to work together with Pytest itself to allow specific parts of an integration test suite to be run and re-run separately to facilitate fast local development.

`pytest-jubilant` does not aim to be the complete solution for charm integration testing. We pick up at the same point that Juju does: performing operations with packed charms. This means that working with unpacked charm files is out of scope, which includes reading `charmcraft.yaml` But if you can do it with Jubilant, then `pytest-jubilant` aims to let you do it cleanly and easily.


## Developing

Jubilant uses [`uv`](https://docs.astral.sh/uv/) to manage Python dependencies and tools, so you'll need to [install uv](https://docs.astral.sh/uv/#installation) to work on the library.

You'll also need `tox` installed with the `tox-uv` plugin. Consider installing it with:
```shell
uv tool install tox --with tox-uv
```

Always run `tox -e format`, `tox -e lint`, and `tox -e unit` locally before pushing.

The following checks are all required in CI:
- `tox -e lint`
- `tox -e unit`
- `tox -e integration`

You'll need to pack the test charms and set up environment variables to point to them before running the integration tests locally.


## Pull requests

Changes are proposed as [pull requests on GitHub](https://github.com/canonical/pytest-jubilant/pulls).

Pull requests should have a short title that follows the [conventional commit style](https://www.conventionalcommits.org/en/) using one of these types:

- chore
- ci
- docs
- feat
- fix
- perf
- refactor
- revert
- test

Some examples:

- feat: add a CLI option to keep models after a test failure
- fix!: correct the return type of the `pack` helper
- docs: clarify how to re-run a single part of the test suite

We consider `pytest-jubilant` too small a project to use scopes, so we don't use them.

Note that the commit messages to the PR's branch do not need to follow the conventional commit format, as these will be squashed into a single commit to `main` using the PR title as the commit message.

To help us review your changes, please rebase your pull request onto the `main` branch before you request a review. If you need to bring in the latest changes from `main` after the review has started, please use a merge commit.


## Releasing

To release a new version of `pytest-jubilant`, create a Github release. The tag chosen will determine the library's version on release. Always include a description of what is included in the new release and why.
