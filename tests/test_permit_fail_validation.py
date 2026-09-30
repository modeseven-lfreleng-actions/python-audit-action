# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Linux Foundation

"""Regression cover for permit_fail failing closed (issue #215).

The audit steps used to be gated on ``permit_fail == 'false'`` and
``permit_fail == 'true'``, so any other value skipped both of them and
the action passed without auditing anything.

The validation script is read out of ``action.yaml`` rather than
copied here, so the tests cannot drift from the implementation.
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


def _steps() -> list[dict]:
    """Return the composite action's steps, read from action.yaml."""
    action = yaml.safe_load((REPO_ROOT / "action.yaml").read_text())
    return action["runs"]["steps"]


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
