"""Crash-recovery reconcile pass (owner-62 / app #115).

reconcile replays the write-ahead journal left by a crashed run, idempotently,
without re-running OCR/LLM. It heals every branch of the Drive-move/JSON-store
window and never deletes a Drive file (soft-delete invariant).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from postmule.agents import reconcile
from postmule.data import journal, records, run_log


class FakeDrive:
    """In-memory storage with stable ids (Google Drive semantics: ids survive move/rename)."""

    def __init__(self, folders):
        # folders: {folder_id: [file_id, ...]}
        self.folders = {k: list(v) for k, v in folders.items()}
        self.renamed = {}
        self.deleted = []

    def list_folder(self, folder_id):
        return [{"id": fid, "name": self.renamed.get(fid, fid)} for fid in self.folders.get(folder_id, [])]

    def move_file(self, file_id, new_folder_id, old_folder_id):
        if file_id in self.folders.get(old_folder_id, []):
            self.folders[old_folder_id].remove(file_id)
        self.folders.setdefault(new_folder_id, []).append(file_id)
        return None  # stable id

    def rename_file(self, file_id, new_name):
        self.renamed[file_id] = new_name
        return None  # stable id

    def delete_file(self, file_id):
        self.deleted.append(file_id)


def _journal_entry(drive_file_id="drv-1", **over):
    entry = {
        "drive_file_id": drive_file_id,
        "src_folder_id": "inbox",
        "dest_folder_id": "bills",
        "suggested_filename": "2025-03-01_ATT_Bill.pdf",
        "category": "Bill",
        "record_payload": {
            "date_received": "2025-03-01",
            "drive_file_id": drive_file_id,
            "amount_due": 10.0,
        },
        "run_id": "crashed-run",
    }
    entry.update(over)
    return entry


_FOLDERS = {"inbox": "inbox", "bills": "bills", "needs_review": "review"}


class TestReconcileBranches:
    def test_record_already_exists_drops_entry(self, tmp_path):
        records.store_record(tmp_path, "Bill", _journal_entry()["record_payload"])
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": [], "bills": ["drv-1"]})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        from postmule.data.bills import load_bills

        assert res["already_present"] == 1
        assert journal.load_pending(tmp_path) == []
        assert len(load_bills(tmp_path, 2025)) == 1

    def test_moved_not_stored_heals_record(self, tmp_path):
        # Crash after Drive move, before JSON commit: file in dest, no record, journal pending.
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": [], "bills": ["drv-1"]})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        from postmule.data.bills import load_bills

        bills = load_bills(tmp_path, 2025)
        assert res["healed"] == 1
        assert len(bills) == 1
        assert bills[0]["drive_file_id"] == "drv-1"
        assert journal.load_pending(tmp_path) == []

    def test_not_moved_redoes_move_and_stores(self, tmp_path):
        # Crash after journal.begin, before the move: file still in inbox.
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": ["drv-1"], "bills": []})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        from postmule.data.bills import load_bills

        assert res["redone"] == 1
        assert "drv-1" in drive.folders["bills"]
        assert "drv-1" not in drive.folders["inbox"]
        assert drive.renamed["drv-1"] == "2025-03-01_ATT_Bill.pdf"
        assert len(load_bills(tmp_path, 2025)) == 1
        assert journal.load_pending(tmp_path) == []

    def test_missing_drive_file_flags_divergence_no_delete(self, tmp_path):
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": [], "bills": []})  # file is in neither folder
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        from postmule.data.bills import load_bills

        assert res["divergent"] == ["drv-1"]
        assert drive.deleted == []  # soft-delete invariant
        assert load_bills(tmp_path, 2025) == []  # no guessed record
        assert journal.load_pending(tmp_path) == [_pending(tmp_path)[0]]  # entry left for review

    def test_unknown_schema_version_flagged_not_acted(self, tmp_path):
        # Simulate an entry written by a future code version (begin always stamps
        # the current version, so write the file directly).
        import json

        d = journal.journal_dir(tmp_path)
        d.mkdir(parents=True, exist_ok=True)
        entry = {**_journal_entry(), "schema_version": 999, "state": "pending"}
        (d / "drv-1.json").write_text(json.dumps(entry), encoding="utf-8")
        drive = FakeDrive({"inbox": ["drv-1"], "bills": []})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        assert res["needs_review"] == ["drv-1"]
        assert "drv-1" in drive.folders["inbox"]  # not moved
        assert journal.load_pending(tmp_path)  # entry kept

    def test_idempotent_run_twice_no_duplicate(self, tmp_path):
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": [], "bills": ["drv-1"]})
        reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        from postmule.data.bills import load_bills

        assert len(load_bills(tmp_path, 2025)) == 1

    def test_empty_folder_ids_flag_divergence(self, tmp_path):
        # Journal entry with no src/dest folder ids: nothing to inspect, flagged.
        journal.begin(tmp_path, _journal_entry(src_folder_id="", dest_folder_id=""))
        drive = FakeDrive({})
        res = reconcile.run_reconcile(drive, {}, tmp_path, "new-run")
        assert res["divergent"] == ["drv-1"]

    def test_never_calls_delete(self, tmp_path):
        journal.begin(tmp_path, _journal_entry())
        drive = MagicMock()
        drive.list_folder.return_value = [{"id": "drv-1", "name": "x"}]
        drive.move_file.return_value = None
        drive.rename_file.return_value = None
        reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        drive.delete_file.assert_not_called()


class TestReconcileRunLog:
    def test_relabels_orphaned_in_progress(self, tmp_path):
        run_log.start_run(tmp_path, {"run_id": "crashed-run", "start_time": "t0"})
        drive = FakeDrive({"inbox": [], "bills": []})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run")
        assert res["crashed_marked"] == 1
        assert run_log.load_run_log(tmp_path)[0]["status"] == "crashed"


class TestReconcileDryRun:
    def test_dry_run_does_nothing(self, tmp_path):
        journal.begin(tmp_path, _journal_entry())
        drive = FakeDrive({"inbox": ["drv-1"], "bills": []})
        res = reconcile.run_reconcile(drive, _FOLDERS, tmp_path, "new-run", dry_run=True)
        assert res == reconcile.empty_result()
        assert journal.load_pending(tmp_path)  # untouched


def _pending(tmp_path):
    return journal.load_pending(tmp_path)


@pytest.fixture(autouse=True)
def _no_real_drive():
    yield
