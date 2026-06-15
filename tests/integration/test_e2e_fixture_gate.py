"""
Integration test for the E2E fixture gate (PLAN section 14.18).

Runs the full daily pipeline against the committed fixture email/PDF using
only local, credential-free providers and checks the v0.1.0 success scenario
from mvp-review.md section 2: one fixture email is fetched, OCR'd, classified,
filed into the correct folder, and recorded in JSON.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from e2e_fixture_run import run_gate  # noqa: E402


def test_e2e_fixture_gate_passes(tmp_path):
    result = run_gate(tmp_path)
    assert result.passed, "\n".join(result.details)
