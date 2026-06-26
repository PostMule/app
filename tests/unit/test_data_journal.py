"""Write-ahead journal for the Drive-move -> JSON-store boundary (owner-62 / app #115).

begin() records an in-flight item atomically before the Drive move; commit()
removes it after the JSON record is stored. A crash leaves the entry on disk for
the next reconcile to replay. The journal holds only in-flight items.
"""

from __future__ import annotations

from postmule.data import journal


def _entry(drive_file_id="drv-1", **over):
    base = {
        "drive_file_id": drive_file_id,
        "src_folder_id": "inbox",
        "dest_folder_id": "bills",
        "suggested_filename": "2025-03-01_ATT_Bill.pdf",
        "category": "Bill",
        "record_payload": {"drive_file_id": drive_file_id, "amount_due": 10.0},
        "run_id": "run-1",
    }
    base.update(over)
    return base


class TestBeginCommit:
    def test_begin_writes_pending_entry(self, tmp_path):
        journal.begin(tmp_path, _entry())
        pending = journal.load_pending(tmp_path)
        assert len(pending) == 1
        assert pending[0]["drive_file_id"] == "drv-1"
        assert pending[0]["state"] == "pending"
        assert pending[0]["schema_version"] == journal.SCHEMA_VERSION

    def test_commit_removes_entry(self, tmp_path):
        journal.begin(tmp_path, _entry())
        journal.commit(tmp_path, "drv-1")
        assert journal.load_pending(tmp_path) == []

    def test_commit_missing_entry_is_noop(self, tmp_path):
        journal.commit(tmp_path, "never-existed")  # no raise

    def test_begin_same_id_twice_keeps_one_entry(self, tmp_path):
        journal.begin(tmp_path, _entry())
        journal.begin(tmp_path, _entry())
        assert len(journal.load_pending(tmp_path)) == 1

    def test_distinct_ids_are_separate_entries(self, tmp_path):
        journal.begin(tmp_path, _entry("a"))
        journal.begin(tmp_path, _entry("b"))
        assert {e["drive_file_id"] for e in journal.load_pending(tmp_path)} == {"a", "b"}


class TestLoadPending:
    def test_empty_when_no_journal_dir(self, tmp_path):
        assert journal.load_pending(tmp_path) == []

    def test_skips_unreadable_entry(self, tmp_path):
        journal.begin(tmp_path, _entry())
        # Corrupt one entry file; load_pending must skip it, not raise.
        bad = journal.journal_dir(tmp_path) / "broken.json"
        bad.write_text("{ not json", encoding="utf-8")
        pending = journal.load_pending(tmp_path)
        assert len(pending) == 1
        assert pending[0]["drive_file_id"] == "drv-1"
