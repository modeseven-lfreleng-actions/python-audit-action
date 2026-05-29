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

### Pinned allow-list via `config` (git, SHA-pinnable)

The `config` input is a GitHub-Actions `uses:`-style coordinate that
identifies a remote allow-list file and fetches it with a shallow,
ref-pinned **git** fetch (rather than an unpinned HTTP download). It
supports branches, tags and commit SHAs, so you can pin the
allow-list to an immutable commit, much like an action pin.

> [!IMPORTANT]
> `config` is **mutually exclusive** with the `allow_list_*` inputs.
> Supplying any of `allow_list_path`, `allow_list_url`,
> `allow_list_org` or `allow_list_disable` together with `config` is
> an error. The `ignore_vulns` input is *not* a source and still
> merges with the IDs loaded via `config`.

```yaml
      - name: "Audit project dependencies"
        uses: lfreleng-actions/python-audit-action@main
        with:
          python_version: ${{ matrix.python-version }}
          config: "lfreleng-actions@v1.0.0"
```

#### `config` grammar

```text
<config> ::= <source> [ "@" <ref> ] [ <ws>+ "#" <comment> ]
<source> ::= [ <host-org> [ "/" <repo> ] ] [ "//" <subpath> ]
```

Defaults applied to anything you omit:

<!-- markdownlint-disable MD013 -->

| Element   | Default                                                             |
| --------- | ------------------------------------------------------------------- |
| host-org  | `github.repository_owner` (when you omit the org)                   |
| repo      | `.github`                                                           |
| directory | `.github/python-audit/<workflow-org>/` then `.github/python-audit/` |
| filename  | `allow_list.txt`                                                    |
| ref       | the host repo's default branch (`HEAD`)                             |

<!-- markdownlint-enable MD013 -->

- The `//` separator splits the repository from the in-repo path
  (the same convention Terraform/go-getter use). Text after `//`:
  - **empty** (or no `//`) — default directory search + default
    filename.
  - **bare filename** (no `/`) — overrides the filename, keeps the
    default directory search.
  - **contains a `/`** — an explicit in-repo path; the action skips
    the search and that exact path must exist.
- One or more spaces then `#` starts a trailing comment, which the
  parser drops (`#`, `#`, `\t#` all work).
- The output `resolved_sha` always reports the commit the ref
  resolved to, even when you pin a branch or tag.

#### Search / fallback chain

When the directory is auto-derived (you did not give an explicit
directory after `//`), the action tries, in order:

1. `.github/python-audit/<workflow-org>/<filename>` (org-specific)
2. `.github/python-audit/<filename>` (host-wide family default)

The first file that exists wins. If neither exists, the action
proceeds with `ignore_vulns` alone (soft, no warning) — consistent
with the default-URL behaviour above. An **explicit** path that is
missing is always a hard error.

#### `config` examples

Assuming the workflow runs in org `onap`:

<!-- markdownlint-disable MD013 -->

| `config` value                         | Fetched from                    | In-repo path (search chain)                                              |
| -------------------------------------- | ------------------------------- | ------------------------------------------------------------------------ |
| `lfreleng-actions@main`                | `lfreleng-actions/.github@main` | `…/python-audit/onap/allow_list.txt` → `…/python-audit/allow_list.txt`   |
| `lfit@v1.1.0`                          | `lfit/.github@v1.1.0`           | same chain                                                               |
| `lfit@ab7a940… # v1.0.0`               | `lfit/.github@<sha>`            | same chain; comment ignored                                              |
| `lfit//custom_list.txt@v1.1.0  # ONAP` | `lfit/.github@v1.1.0`           | `…/python-audit/onap/custom_list.txt` → `…/python-audit/custom_list.txt` |
| `lfit//@ab7a940…`                      | `lfit/.github@<sha>`            | default chain + `allow_list.txt`                                         |
| `lfit//configs/onap/list.txt@main`     | `lfit/.github@main`             | `configs/onap/list.txt` (explicit; no search)                            |
| `//team_list.txt@main`                 | `onap/.github@main`             | `…/python-audit/onap/team_list.txt` → `…/python-audit/team_list.txt`     |

<!-- markdownlint-enable MD013 -->

#### Private host repositories

For a private host-org `.github` repo, pass a token with
`contents:read` on that repo. `GITHUB_TOKEN` grants access to the
current repository alone, so pass a PAT or GitHub App token here:

```yaml
        with:
          python_version: ${{ matrix.python-version }}
          config: "my-private-org@v2.0.0"
          token: ${{ secrets.CONFIG_READ_TOKEN }}
```

#### `config` outputs

Using `config` makes the action expose: `resolved_host_org`,
`resolved_repo`, `resolved_ref`, `resolved_sha`, `resolved_path` and
`matched_candidate`. Use `resolved_sha` to record or assert which
commit supplied the allow-list.

> [!NOTE]
> `config` resolution uses the runner's preinstalled `python3` (the
> resolver needs no third-party packages). GitHub-hosted runners
> ship it; on self-hosted runners `python3` must sit on `PATH`. Both
> repositories mirror the shared parser
> `src/resolve_config_source.py`, and changes must land as paired
> pull requests across `python-audit-action` and
> `harden-runner-block-action`.

#### Suppressing the step summary on matrix jobs

Each matrix leg is a separate job with its own step summary, so the
allow-list block repeats once per leg. An action cannot detect the
matrix context itself, but the calling workflow can. Set
`allow_list_summary` so a single leg emits the block:

```yaml
        with:
          python_version: ${{ matrix.python-version }}
          # Emit the allow-list summary from the first matrix leg.
          allow_list_summary: ${{ strategy.job-index == 0 }}
```

Outside a matrix, `strategy.job-index` is empty; use
`${{ !strategy.job-total || strategy.job-index == 0 }}` if a single
template must cover both matrix and non-matrix jobs.

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
| config             | False    | ""        | `uses:`-style coordinate for a git-fetched, SHA-pinnable allow-list. Mutually exclusive with the `allow_list_*` inputs. See above.                           |
| token              | False    | ""        | Token with `contents:read` for fetching a private host repo via `config`. Leave empty for public repos.                                                      |
| allow_list_summary | False    | True      | Write the allow-list/config block to the job step summary. Set `false` to suppress (e.g. on matrix legs other than the first). See note below.               |

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
