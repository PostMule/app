"""Sanity checks for setup.sh (macOS/Linux install contract counterpart to setup.ps1)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SETUP_SH = ROOT / "setup.sh"


def test_setup_sh_exists() -> None:
    assert SETUP_SH.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_setup_sh_has_valid_bash_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SETUP_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_setup_sh_rejects_unknown_flag() -> None:
    result = subprocess.run(
        ["bash", str(SETUP_SH), "--not-a-real-flag"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unknown option" in result.stderr
