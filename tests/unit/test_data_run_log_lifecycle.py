"""Run-log lifecycle markers for crash tracing (owner-62 / app #115).

A run writes an in-progress marker at start and finalizes it at end. A run that
crashes leaves an orphaned in-progress entry, which the next reconcile relabels
to 'crashed'. finalize updates the existing entry in place rather than appending
a duplicate.
"""

from __future__ import annotations

from postmule.data import run_log


class TestStartRun:
    def test_writes_in_progress_marker(self, tmp_path):
        run_log.start_run(tmp_path, {"run_id": "r1", "start_time": "t0"})
        entries = run_log.load_run_log(tmp_path)
        assert len(entries) == 1
        assert entries[0]["status"] == "in-progress"
        assert entries[0]["run_id"] == "r1"


class TestFinalizeRun:
    def test_updates_existing_entry_in_place(self, tmp_path):
        run_log.start_run(tmp_path, {"run_id": "r1", "start_time": "t0"})
        run_log.finalize_run(tmp_path, {"run_id": "r1", "start_time": "t0", "status": "success"})
        entries = run_log.load_run_log(tmp_path)
        assert len(entries) == 1
        assert entries[0]["status"] == "success"

    def test_appends_when_no_marker(self, tmp_path):
        run_log.finalize_run(tmp_path, {"run_id": "r2", "status": "failed"})
        entries = run_log.load_run_log(tmp_path)
        assert len(entries) == 1
        assert entries[0]["status"] == "failed"


class TestMarkStaleCrashed:
    def test_relabels_orphaned_in_progress(self, tmp_path):
        run_log.start_run(tmp_path, {"run_id": "old", "start_time": "t0"})
        n = run_log.mark_stale_in_progress_crashed(tmp_path, current_run_id="new")
        entries = run_log.load_run_log(tmp_path)
        assert n == 1
        assert entries[0]["status"] == "crashed"

    def test_excludes_current_run(self, tmp_path):
        run_log.start_run(tmp_path, {"run_id": "current", "start_time": "t0"})
        n = run_log.mark_stale_in_progress_crashed(tmp_path, current_run_id="current")
        assert n == 0
        assert run_log.load_run_log(tmp_path)[0]["status"] == "in-progress"

    def test_leaves_finalized_entries_alone(self, tmp_path):
        run_log.finalize_run(tmp_path, {"run_id": "done", "status": "success"})
        n = run_log.mark_stale_in_progress_crashed(tmp_path, current_run_id="new")
        assert n == 0
        assert run_log.load_run_log(tmp_path)[0]["status"] == "success"
