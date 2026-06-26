"""Idempotency-by-drive_file_id for the JSON data layer (owner-62 / app #115).

A crash-replay or a double pipeline run must not create a second record for a
file that is already stored. The add_* functions dedupe on a non-empty
drive_file_id; records without one always append (they cannot be deduped).
"""

from __future__ import annotations

from postmule.data import bills as bills_data
from postmule.data import forward_to_me as ftm_data
from postmule.data import notices as notices_data
from postmule.data import records


class TestAddBillIdempotent:
    def test_second_add_same_drive_file_id_is_noop(self, tmp_path):
        rec = {"date_received": "2025-03-01", "drive_file_id": "drv-1", "amount_due": 10.0}
        first = bills_data.add_bill(tmp_path, dict(rec))
        second = bills_data.add_bill(tmp_path, dict(rec))
        bills = bills_data.load_bills(tmp_path, 2025)
        assert len(bills) == 1
        # Returns the already-stored record, with its original id preserved.
        assert second["id"] == first["id"]

    def test_records_without_drive_file_id_always_append(self, tmp_path):
        bills_data.add_bill(tmp_path, {"date_received": "2025-03-01", "drive_file_id": ""})
        bills_data.add_bill(tmp_path, {"date_received": "2025-03-01", "drive_file_id": ""})
        assert len(bills_data.load_bills(tmp_path, 2025)) == 2

    def test_distinct_drive_file_ids_both_stored(self, tmp_path):
        bills_data.add_bill(tmp_path, {"date_received": "2025-03-01", "drive_file_id": "a"})
        bills_data.add_bill(tmp_path, {"date_received": "2025-03-01", "drive_file_id": "b"})
        assert len(bills_data.load_bills(tmp_path, 2025)) == 2


class TestAddNoticeIdempotent:
    def test_second_add_same_drive_file_id_is_noop(self, tmp_path):
        rec = {"date_received": "2025-03-01", "drive_file_id": "drv-9"}
        notices_data.add_notice(tmp_path, dict(rec))
        notices_data.add_notice(tmp_path, dict(rec))
        assert len(notices_data.load_notices(tmp_path, 2025)) == 1


class TestAddItemIdempotent:
    def test_second_add_same_drive_file_id_is_noop(self, tmp_path):
        rec = {"date_received": "2025-03-01", "drive_file_id": "drv-7"}
        ftm_data.add_item(tmp_path, dict(rec))
        ftm_data.add_item(tmp_path, dict(rec))
        assert len(ftm_data.load_forward_to_me(tmp_path)) == 1


class TestRecordsHelper:
    def test_store_record_dispatches_by_category(self, tmp_path):
        records.store_record(
            tmp_path, "Bill", {"date_received": "2025-03-01", "drive_file_id": "b1"}
        )
        records.store_record(
            tmp_path, "Notice", {"date_received": "2025-03-01", "drive_file_id": "n1"}
        )
        records.store_record(
            tmp_path, "ForwardToMe", {"date_received": "2025-03-01", "drive_file_id": "f1"}
        )
        assert len(bills_data.load_bills(tmp_path, 2025)) == 1
        assert len(notices_data.load_notices(tmp_path, 2025)) == 1
        assert len(ftm_data.load_forward_to_me(tmp_path)) == 1

    def test_store_record_unknown_category_is_noop(self, tmp_path):
        records.store_record(tmp_path, "Junk", {"drive_file_id": "j1"})
        assert bills_data.load_bills(tmp_path, 2025) == []

    def test_record_exists_for_drive_file(self, tmp_path):
        assert records.record_exists_for_drive_file(tmp_path, "x1") is False
        bills_data.add_bill(tmp_path, {"date_received": "2025-03-01", "drive_file_id": "x1"})
        assert records.record_exists_for_drive_file(tmp_path, "x1") is True

    def test_record_exists_finds_notice_and_ftm(self, tmp_path):
        notices_data.add_notice(tmp_path, {"date_received": "2025-03-01", "drive_file_id": "n2"})
        ftm_data.add_item(tmp_path, {"date_received": "2025-03-01", "drive_file_id": "f2"})
        assert records.record_exists_for_drive_file(tmp_path, "n2") is True
        assert records.record_exists_for_drive_file(tmp_path, "f2") is True

    def test_record_exists_empty_id_is_false(self, tmp_path):
        assert records.record_exists_for_drive_file(tmp_path, "") is False
