# Releases and PyPI

The workflow is `.github/workflows/ci.yml` (Tests, version tag and PyPI).
It runs tests on Python 3.10–3.14, builds source and wheel distributions, and
validates documentation. Pull requests cannot publish or create tags.

## One-time configuration

In the existing PyPI project `updownio`, open **Publishing**, then add a GitHub
Trusted Publisher with these exact values:

| Field | Value |
| --- | --- |
| PyPI project | `updownio` |
| Owner | `decryptus` |
| Repository | `updownio` |
| Workflow filename | `ci.yml` |
| Environment | `pypi` |

If the project does not yet exist, use PyPI's pending publisher form instead.
In GitHub, configure the `pypi` environment if you want branch restrictions or
reviewer approval. No API token secret is required. Only the publishing job has
`id-token: write`; it downloads the built artifact without checking out code.
Only the tag job has `contents: write`.

## New version

1. Update `VERSION`, `RELEASE`, and both version fields in `setup.yml` together.
   Add release notes to `CHANGELOG`. Use a stable `X.Y.Z` version.
2. Open a pull request and merge to `main` after CI succeeds.
3. The workflow creates the missing tag after tests and documentation checks.
4. It checks out the selected commit, runs its tests, builds distributions,
   validates them with Twine and publishes to PyPI.

The publish job is part of the same workflow because a tag created with
`GITHUB_TOKEN` does not trigger a second push workflow. Ordinary later commits
with the same version do not move the old tag or publish new contents under it.
Explicitly pushed tags must match the version files and belong to `main` history.

## Retry

If Trusted Publishing was not configured, configure it and rerun the failed
publishing job. Alternatively, run the workflow manually **from main** with
`tag` set to the existing tag (for example `v0.1.0`). Its commit must belong to
main history and its version files must match. The tagged source is rebuilt;
artifacts are not built from the current main version by mistake.

Publication is serialized and existing files are skipped. PyPI does not allow
replacing published files; use a new version for any changed package contents.

## Local validation

Build in isolation with `python -m build`, which also rebuilds the wheel from the
source archive. Run `python -m twine check --strict dist/*`. Install the wheel in
a clean environment outside the checkout, then run `python -m pip check`.

No publication is performed by local tests or builds.
