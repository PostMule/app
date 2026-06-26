"""Keystone crash-recovery integration test (owner-62 / app #115).

Kills the pipeline between the Drive move and the JSON store, then re-runs and
asserts Drive and the JSON source of truth end consistent: zero file loss, zero
double-processing. Also covers the run-lock skip path and reconcile wiring.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest
import yaml

from postmule.agents.classification import ProcessedMail
from postmule.agents.email_ingestion import IngestedPDF, IngestionResult
from postmule.core.config import load_config
from postmule.data import journal
from postmule.data.bills import load_bills
from postmule.data.run_log import load_run_log
from postmule.pipeline import Providers, run_daily_pipeline


class StatefulDrive:
    """In-memory Drive with stable ids (Google Drive: ids survive move/rename)."""

    def __init__(self):
        self.folders = {"inbox": ["f1"], "bills": [], "review": [], "dupes": []}
        self.renamed = {}

    def list_folder(self, folder_id):
        return [
            {"id": fid, "name": self.renamed.get(fid, fid)}
            for fid in self.folders.get(folder_id, [])
        ]

    def move_file(self, file_id, new_folder_id, old_folder_id):
        if file_id in self.folders.get(old_folder_id, []):
            self.folders[old_folder_id].remove(file_id)
        self.folders.setdefault(new_folder_id, []).append(file_id)
        return None

    def rename_file(self, file_id, new_name):
        self.renamed[file_id] = new_name
        return None

    def delete_file(self, file_id):  # pragma: no cover - must never be called
        raise AssertionError("reconcile must never delete a Drive file")


@pytest.fixture
def cfg(tmp_path):
    data = {
        "app": {"dry_run": False, "install_dir": str(tmp_path)},
        "notifications": {"alert_email": "test@example.com"},
        "llm": {"providers": [{"service": "gemini", "enabled": True}]},
        "email": {"providers": [{"service": "gmail", "enabled": True, "address": "a@b.c"}]},
        "storage": {"providers": [{"service": "google_drive", "enabled": True}]},
        "data_protection": {"max_files_moved_per_run": 50},
        "deployment": {"dashboard_port": 5000},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data), encoding="utf-8")
    return load_config(path)


@pytest.fixture
def credentials():
    return {"gemini": {"api_key": "k"}, "smtp": {"host": "h", "username": "u", "password": "p"}}


def _providers(drive):
    from unittest.mock import MagicMock

    gmail = MagicMock()
    sheets = MagicMock()
    llm = MagicMock()
    safety = MagicMock()
    safety.summary.return_value = {}
    folder_ids = {
        "root": "r", "inbox": "inbox", "bills": "bills",
        "needs_review": "review", "duplicates": "dupes",
    }
    return Providers(
        drive=drive, sheets=sheets, llm=llm, safety_agent=safety,
        folder_ids=folder_ids, mailbox_notification_providers=[gmail],
    )


def _bill_mail(pdf):
    return ProcessedMail(
        original_path=pdf, category="Bill", confidence=0.95, sender="ATT",
        recipients=["Alice"], amount_due=94.0, due_date="2025-04-05",
        account_number=None, summary="Monthly bill", ocr_text="",
        ocr_method="pdfplumber", processed_date="2025-03-01",
        suggested_filename="2025-03-01_Alice_ATT_Bill.pdf",
        destination_folder="Bills", tokens_used=0,
    )


@contextmanager
def _run_env(cfg, drive, pdf, ingest_result, crash_store=False):
    providers = _providers(drive)
    with patch("postmule.pipeline._build_providers", return_value=providers), patch(
        "postmule.agents.email_ingestion.run_ingestion", return_value=ingest_result
    ), patch("postmule.agents.classification.classify_pdf", return_value=_bill_mail(pdf)), patch(
        "postmule.agents.integrity.duplicate_detector.run_duplicate_detection", return_value={}
    ), patch("postmule.agents.summary._send_email"):
        if crash_store:
            with patch(
                "postmule.pipeline._store_processed_mail",
                side_effect=RuntimeError("simulated crash before JSON commit"),
            ):
                yield
        else:
            yield


def test_crash_between_move_and_store_is_healed_on_rerun(cfg, credentials, tmp_path):
    drive = StatefulDrive()
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ingested = IngestedPDF(
        filename="scan.pdf", local_path=pdf, source_email_id="m1",
        received_date="2025-03-01", drive_file_id="f1",
    )
    first_ingest = IngestionResult(emails_found=1, pdfs_saved=1, pdfs_uploaded=1, ingested=[ingested])

    # Run 1: Drive move succeeds, JSON store crashes -> divergence.
    with _run_env(cfg, drive, pdf, first_ingest, crash_store=True):
        run_daily_pipeline(cfg, credentials, tmp_path, dry_run=False)

    assert "f1" in drive.folders["bills"], "file should have been moved on Drive"
    assert "f1" not in drive.folders["inbox"]
    pending = journal.load_pending(tmp_path)
    assert len(pending) == 1 and pending[0]["drive_file_id"] == "f1"
    assert load_bills(tmp_path, 2025) == [], "no JSON record yet (store crashed)"
    assert load_run_log(tmp_path), "run left a trace"

    # Run 2: nothing new to ingest; reconcile at start heals the journaled item.
    empty_ingest = IngestionResult(emails_found=0, pdfs_saved=0, pdfs_uploaded=0, ingested=[])
    with _run_env(cfg, drive, pdf, empty_ingest, crash_store=False):
        run_daily_pipeline(cfg, credentials, tmp_path, dry_run=False)

    bills = load_bills(tmp_path, 2025)
    assert len(bills) == 1, "exactly one record after heal — zero loss, zero double-count"
    assert bills[0]["drive_file_id"] == "f1"
    assert drive.folders["bills"].count("f1") == 1, "not re-moved / duplicated on Drive"
    assert journal.load_pending(tmp_path) == [], "journal cleared after heal"


def test_second_overlapping_run_is_skipped(cfg, credentials, tmp_path):
    from postmule.core.run_lock import PipelineLockHeld

    with patch("postmule.pipeline.run_lock") as mock_lock:
        mock_lock.return_value.__enter__.side_effect = PipelineLockHeld("held")
        stats = run_daily_pipeline(cfg, credentials, tmp_path, dry_run=False)
    assert stats["status"] == "skipped"
    assert load_run_log(tmp_path) == [], "a skipped run does not record a run-log entry"


def test_clean_run_leaves_empty_journal(cfg, credentials, tmp_path):
    drive = StatefulDrive()
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ingested = IngestedPDF(
        filename="scan.pdf", local_path=pdf, source_email_id="m1",
        received_date="2025-03-01", drive_file_id="f1",
    )
    result = IngestionResult(emails_found=1, pdfs_saved=1, pdfs_uploaded=1, ingested=[ingested])
    with _run_env(cfg, drive, pdf, result, crash_store=False):
        run_daily_pipeline(cfg, credentials, tmp_path, dry_run=False)
    assert journal.load_pending(tmp_path) == [], "a healthy run commits every journal entry"
    assert len(load_bills(tmp_path, 2025)) == 1
