# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Linux Foundation

"""Regression cover for permit_fail (issues #215 and #216).

The audit steps used to be gated on ``permit_fail == 'false'`` and
``permit_fail == 'true'``, so any other value skipped both of them and
the action passed without auditing anything (#215).

With ``permit_fail: true`` the action passes whatever the audit finds,
so nothing showed that the audit had run at all (#216). The
``audit_outcome`` output reports the outcome of whichever audit step
ran, and the workflow tests assert on it end to end.

The validation script and output are read out of ``action.yaml``
rather than copied here, so the tests cannot drift from the
implementation.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_STEP = "Validate permit_fail input"
AUDIT_STEP = "Auditing with: pypa/gh-action-pip-audit"
AUDIT_OUTCOME = "audit_outcome"


def _action() -> dict:
    """Return the parsed action.yaml."""
    return yaml.safe_load((REPO_ROOT / "action.yaml").read_text())


def _steps() -> list[dict]:
    """Return the composite action's steps, read from action.yaml."""
    return _action()["runs"]["steps"]


def _audit_step_ids() -> list[str | None]:
    """Return the id of each audit step, None where it has none."""
    return [s.get("id") for s in _steps() if s.get("name") == AUDIT_STEP]


def _run_validation(value: str) -> subprocess.CompletedProcess[str]:
    """Run the validation step's script with PERMIT_FAIL set to value."""
    script = next(s["run"] for s in _steps() if s.get("name") == VALIDATE_STEP)
    env = dict(os.environ)
    env["PERMIT_FAIL"] = value
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.mark.parametrize("value", ["true", "false", "TRUE", "False", "tRuE"])
def test_recognised_values_pass(value):
    """Values the audit-step expressions recognise are accepted."""
    proc = _run_validation(value)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "::error::" not in proc.stdout


@pytest.mark.parametrize(
    "value",
    ["", "yes", "no", "0", "1", "on", " true", "true ", "true\n", "falsey"],
)
def test_unrecognised_values_fail(value):
    """Anything the expressions would not match is rejected."""
    proc = _run_validation(value)
    assert proc.returncode != 0, f"accepted permit_fail={value!r}"
    assert "::error::Invalid permit_fail value" in proc.stdout, proc.stdout


def test_error_cannot_inject_workflow_command():
    """An embedded newline is not echoed raw into the log."""
    proc = _run_validation("yes\n::warning::injected")
    assert proc.returncode != 0
    assert "\n::warning::injected" not in proc.stdout, proc.stdout


def test_validation_runs_before_anything_else():
    """A bad value fails before any download, install or audit."""
    assert _steps()[0].get("name") == VALIDATE_STEP


def test_audit_gates_are_complementary():
    """Exactly one audit step runs for any value, strict by default.

    Defence in depth: should validation ever be bypassed, a value
    other than 'true' still runs the strict audit.
    """
    gates = sorted(s["if"] for s in _steps() if s.get("name") == AUDIT_STEP)
    assert gates == [
        "${{ inputs.permit_fail != 'true' }}",
        "${{ inputs.permit_fail == 'true' }}",
    ], gates


def test_audit_steps_have_distinct_ids():
    """audit_outcome can only read an audit step that has its own id."""
    ids = _audit_step_ids()
    assert len(ids) == 2, ids
    assert all(ids), ids
    assert len(set(ids)) == len(ids), ids


def test_audit_outcome_reads_each_audit_step_outcome():
    """audit_outcome reports the outcome of whichever audit step ran.

    It must read ``outcome``, not ``conclusion``: continue-on-error
    turns the permitted step's conclusion into 'success' even when the
    audit failed, which would hide the failure the output exists to
    report.
    """
    value = _action()["outputs"][AUDIT_OUTCOME]["value"]
    for step_id in _audit_step_ids():
        assert f"steps.{step_id}.outcome" in value, value
    assert ".conclusion" not in value, value
