"""Single-instance pipeline run lock (owner-62 / app #115).

The lock is an OS byte-range lock on a held-open file: a second live holder is
refused, and the lock is released automatically when the holder exits or dies —
no stale-lock cleanup. dry_run never contends for the lock.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

from postmule.core import run_lock as rl


class TestAcquireRelease:
    def test_acquire_yields_then_releases(self, tmp_path):
        with rl.run_lock(tmp_path):
            pass
        # Re-acquire after release succeeds.
        with rl.run_lock(tmp_path):
            pass

    def test_second_acquire_refused_while_held(self, tmp_path):
        with rl.run_lock(tmp_path):
            with pytest.raises(rl.PipelineLockHeld):
                with rl.run_lock(tmp_path):
                    pass

    def test_granted_again_after_release(self, tmp_path):
        with rl.run_lock(tmp_path):
            pass
        with rl.run_lock(tmp_path):  # no raise
            pass

    def test_records_diagnostics(self, tmp_path):
        with rl.run_lock(tmp_path):
            info = rl.read_lock_info(tmp_path)
        assert info is not None
        assert info["pid"] == os.getpid()
        assert info["start_time"]

    def test_read_lock_info_none_when_absent(self, tmp_path):
        assert rl.read_lock_info(tmp_path) is None

    def test_read_lock_info_none_when_corrupt(self, tmp_path):
        (tmp_path / "pipeline.lock").write_text("{ not json", encoding="utf-8")
        assert rl.read_lock_info(tmp_path) is None


class TestDryRun:
    def test_dry_run_does_not_contend(self, tmp_path):
        with rl.run_lock(tmp_path, dry_run=True):
            with rl.run_lock(tmp_path, dry_run=True):
                pass

    def test_dry_run_writes_no_lock_file(self, tmp_path):
        with rl.run_lock(tmp_path, dry_run=True):
            pass
        assert not (tmp_path / "pipeline.lock").exists()


_CHILD = """
import sys, time
from pathlib import Path
from postmule.core import run_lock as rl
data_dir = Path(sys.argv[1])
ready = Path(sys.argv[2])
with rl.run_lock(data_dir):
    ready.write_text("up")
    time.sleep(30)
"""


@pytest.mark.skipif(rl._LOCKING is None, reason="OS byte lock unavailable on this platform")
class TestCrossProcess:
    def test_lock_released_when_holder_process_dies(self, tmp_path):
        ready = tmp_path / "ready"
        env = {**os.environ, "PYTHONPATH": os.getcwd()}
        child = subprocess.Popen([sys.executable, "-c", _CHILD, str(tmp_path), str(ready)], env=env)
        try:
            deadline = time.time() + 15
            while not ready.exists() and time.time() < deadline:
                if child.poll() is not None:
                    pytest.fail("child exited before acquiring the lock")
                time.sleep(0.1)
            assert ready.exists(), "child never acquired the lock"
            # While the child holds it, this process is refused.
            with pytest.raises(rl.PipelineLockHeld):
                with rl.run_lock(tmp_path):
                    pass
        finally:
            child.kill()
            child.wait(timeout=10)
        # The OS released the lock on the child's death — a fresh acquire succeeds.
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                with rl.run_lock(tmp_path):
                    break
            except rl.PipelineLockHeld:
                time.sleep(0.1)
        else:
            pytest.fail("lock was not released after the holder died")
