# Delinea Secret Server AWX Credential Plugin

Custom AWX/AAP managed credential plugin for Delinea (Thycotic) Secret Server.

## Do I need `credential_type` YAML files?

No, not for the managed plugin itself.

This package follows the AWX custom credential plugin pattern:
- it exposes a `CredentialPlugin` object through Python entry points;
- input schema is defined in Python (`inputs`);
- AWX discovers and registers it using `awx-manage setup_managed_credential_types`.

The `credential_type/` YAML files can be kept only as reference/manual fallback, but they are not required for plugin operation.

## Install

```bash
pip install awx-delinea-secret-server-credential-plugin
```

Then on AWX node(s):

```bash
awx-manage setup_managed_credential_types
```

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## GitHub Trusted Publishing (recommended)

This repository uses PyPI Trusted Publishing via GitHub OIDC, so no API token secrets are required.

Create two publishing configurations:
- On PyPI for project `awx-delinea-secret-server-credential-plugin`
- On TestPyPI for the same project name

Use these values in both PyPI and TestPyPI trusted publisher settings:
- Owner: your GitHub org/user
- Repository: `tss-credential-plugin`
- Workflow: `release.yml`
- Environment: `pypi` (for production), `testpypi` (for TestPyPI)

Publish triggers:
- TestPyPI: pushes to `develop` via `release.yml`
- PyPI + GitHub Release: strict semantic tags `vX.Y.Z` (example: `v0.2.0`) via `release.yml`

CI checks (tests/lint/build validation) run in `ci.yml` on `main`, `develop`, and pull requests.

Release notes are populated from `CHANGELOG.md`.
