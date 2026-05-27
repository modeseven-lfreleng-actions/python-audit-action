<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 🐍 Python Dependency Audit

Check a Python project's dependencies for known security vulnerabilities.

## python-audit-action

## Usage Example

<!-- markdownlint-disable MD046 -->

Below is a sample matrix job configuration for this action:

```yaml
  python-audit:
    name: "Python Audit"
    runs-on: "ubuntu-24.04"
    needs:
      - python-build
    # Matrix job
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.python-build.outputs.matrix_json) }}
    permissions:
      contents: read
    steps:
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
```

<!-- markdownlint-enable MD046 -->

Before the audit shown above, a Python build job has run (not shown).

### Multi-Architecture Example

When auditing builds for different architectures, use the `artefact_name` input
to download the correct architecture-specific artefacts:

<!-- markdownlint-disable MD046 -->

```yaml
  python-audit-x64:
    name: "Python Audit x64"
    runs-on: "ubuntu-latest"
    needs: python-build-x64
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.python-build-x64.outputs.matrix_json) }}
    steps:
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          artefact_name: my-package-x64

  python-audit-arm64:
    name: "Python Audit ARM64"
    runs-on: "ubuntu-24.04-arm"
    needs: python-build-arm64
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.python-build-arm64.outputs.matrix_json) }}
    steps:
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          artefact_name: my-package-arm64
```

<!-- markdownlint-enable MD046 -->

## Usage Examples

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
```

### Bypass the default behaviour

To audit all vulnerabilities and bypass default exclusions:

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          ignore_vulns: ""  # Empty string clears defaults
```

### Ignoring Specific Vulnerabilities

To ignore specific vulnerabilities:

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          ignore_vulns: "GHSA-4xh5-x5gv-qwph CVE-2024-XXXX-YYYY"
```

### Centrally managed allow-list (recommended)

The action can load a vulnerability allow-list from a file hosted in
the organisation's `.github` repository. With no `allow_list_*`
inputs supplied, the action attempts to fetch:

```text
https://raw.githubusercontent.com/<org>/.github/HEAD/.github/python-audit/<org>/allow_list.txt
```

where `<org>` defaults to `github.repository_owner`. IDs from this
file merge with whatever the caller passes in `ignore_vulns` (with
duplicates removed).

This behaviour is automatic: when the default URL returns a 404
(no central file published) the action proceeds with the
`ignore_vulns` input alone, without emitting a warning. An
explicitly-supplied `allow_list_path` or `allow_list_url` that
fails to load is a hard error.

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          # No allow_list_* inputs: defaults to the org's .github file.
```

To load from a local file (highest precedence; overrides URL and org):

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          allow_list_path: ".github/python-audit/${{ github.repository_owner }}/allow_list.txt"
```

To load from an explicit URL:

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          allow_list_url: "https://example.com/python-audit-allow-list.txt"
```

To opt out of allow-list loading entirely:

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          allow_list_disable: "true"
```

#### Allow-list file format

Whitespace-separated vulnerability IDs. `#` introduces a comment
(full-line or trailing). The parser skips blank lines. Each token
must match one of:

- `CVE-YYYY-NNNN[N...]`
- `GHSA-xxxx-xxxx-xxxx` (lowercase alphanumerics)
- `PYSEC-YYYY-N+`
- `OSV-YYYY-N+`
- `PVE-N+`

Any token that does not match one of these patterns fails the step
rather than passing through unrecognised.

Example file (e.g.
`.github/python-audit/lfreleng-actions/allow_list.txt`):

```text
# lfreleng-actions: globally allow-listed Python audit vulnerabilities

# pip: malicious sdist link traversal (no fix in shipped pip versions)
GHSA-4xh5-x5gv-qwph

# pyjwt: disputed by upstream; key length is the application's
# responsibility, not the library's.
PYSEC-2025-183
```

## Inputs

<!-- markdownlint-disable MD013 -->

| Variable Name      | Required | Default   | Description                                                                                                                                                  |
| ------------------ | -------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| python_version     | True     | N/A       | Matrix job Python version                                                                                                                                    |
| artefact_name      | False    |           | Custom name for downloaded artefacts (defaults to project name). Useful when building for different platforms/architectures to avoid artefact name conflicts |
| permit_fail        | False    | False     | Continue/pass even when the audit fails                                                                                                                      |
| artefact_path      | False    | "dist"    | Path/location to build artefacts                                                                                                                             |
| summary            | False    | True      | Whether pypa/gh-action-pip-audit generates summary output                                                                                                    |
| path_prefix        | False    | ""        | Path/directory to Python project code                                                                                                                        |
| ignore_vulns       | False    | See below | Vulnerability IDs to ignore (whitespace separated). Merged with allow-list IDs.                                                                              |
| allow_list_path    | False    |           | Local path to allow-list file. Highest precedence; overrides URL and org.                                                                                    |
| allow_list_url     | False    |           | Explicit HTTPS URL to fetch the allow-list from. The action ignores this when `allow_list_path` has a value.                                                 |
| allow_list_org     | False    |           | Org used to construct the default allow-list URL. Defaults to `github.repository_owner`.                                                                     |
| allow_list_disable | False    | False     | Skip allow-list loading entirely.                                                                                                                            |

<!-- markdownlint-enable MD013 -->

## Audit Implementation

The audit process uses an external public action:

[https://github.com/pypa/gh-action-pip-audit](https://github.com/pypa/gh-action-pip-audit)

## Ignored Vulnerabilities

Security flaws in common Python infrastructure packages can cause widespread
failures of workflows. Specific vulnerabilities get added to the table
below to prevent audits from causing widespread workflow failures/blocking.

<!-- markdownlint-disable MD013 -->

| Package | Version | Vulnerability       | Description                                                                                        |
| ------- | ------- | ------------------- | -------------------------------------------------------------------------------------------------- |
| pip     | 25.2    | GHSA-4xh5-x5gv-qwph | A malicious sdist can include links that escape the target directory and overwrite arbitrary files |

<!-- markdownlint-enable MD013 -->
