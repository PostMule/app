"""
PostMule E2E fixture gate (PLAN section 14.18 / mvp-review.md section 2).

Runs the full daily pipeline against one committed fixture email/PDF using
local-only providers (LocalStorageProvider, NoneSpreadsheetProvider, and an
in-memory fixture email + LLM provider) — no live credentials, no real
network calls. On success, writes validation/e2e-fixture-<ts>.log containing
the line E2E_PASS.

Run: python scripts/e2e_fixture_run.py
"""

from __future__ import annotations

import logging
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from postmule.core.config import Config  # noqa: E402
from postmule.data import bills as bills_data  # noqa: E402
from postmule.pipeline import Providers, run_daily_pipeline  # noqa: E402
from postmule.providers import HealthResult  # noqa: E402
from postmule.providers.email.base import EmailMessage  # noqa: E402
from postmule.providers.llm.base import ClassificationResult  # noqa: E402
from postmule.providers.spreadsheet.none import NoneSpreadsheetProvider  # noqa: E402
from postmule.providers.storage.local import LocalStorageProvider  # noqa: E402

FIXTURE_PDF = REPO_ROOT / "tests" / "fixtures" / "e2e" / "sample_bill.pdf"

EXPECTED_SENDER = "Acme Utilities"
EXPECTED_RECIPIENTS = ["Alice Example"]
EXPECTED_AMOUNT_DUE = 84.50
EXPECTED_DUE_DATE = "2026-07-15"
EXPECTED_ACCOUNT_NUMBER = "9988776655"

EXPECTED = {
    "sender": EXPECTED_SENDER,
    "recipients": EXPECTED_RECIPIENTS,
    "amount_due": EXPECTED_AMOUNT_DUE,
    "due_date": EXPECTED_DUE_DATE,
    "account_number": EXPECTED_ACCOUNT_NUMBER,
}


class FixtureEmailProvider:
    """In-memory email provider that returns the fixture email exactly once."""

    def __init__(self, pdf_path: Path) -> None:
        self._pdf_bytes = pdf_path.read_bytes()
        self._served = False

    def list_unprocessed_emails(
        self, sender_filter: str, subject_filter: str
    ) -> list[EmailMessage]:
        if self._served:
            return []
        self._served = True
        return [
            EmailMessage(
                message_id="e2e-fixture-msg-1",
                subject="[Scan Request] Fixture scan",
                received_date="2026-06-14",
                sender="noreply@virtualpostmail.com",
                attachments=[{"name": "sample_bill.pdf", "data": self._pdf_bytes}],
            )
        ]

    def list_emails_with_pdf_attachments(self) -> list[EmailMessage]:
        return []

    def mark_as_processed(self, message_id: str) -> None:
        pass

    def health_check(self) -> HealthResult:
        return HealthResult(ok=True, status="ok", message="fixture email provider")


class FixtureLLMProvider:
    """Canned classifier result — no API key, no network call."""

    def classify(
        self, ocr_text: str, known_names=None, dry_run: bool = False
    ) -> ClassificationResult:
        return ClassificationResult(
            category="Bill",
            confidence=0.95,
            sender=EXPECTED_SENDER,
            recipients=EXPECTED_RECIPIENTS,
            amount_due=EXPECTED_AMOUNT_DUE,
            due_date=EXPECTED_DUE_DATE,
            account_number=EXPECTED_ACCOUNT_NUMBER,
            summary="Fixture utility bill",
            tokens_used=0,
        )

    def health_check(self) -> HealthResult:
        return HealthResult(ok=True, status="ok", message="fixture LLM provider")


def _build_fixture_config(tmp_path: Path) -> Config:
    data = {
        "app": {"dry_run": False},
        "notifications": {"alert_email": "e2e@example.invalid"},
        "llm": {
            "providers": [{"service": "gemini", "enabled": True}],
            "classification_confidence_threshold": 0.80,
        },
        "email": {
            "providers": [{"service": "gmail", "enabled": True, "id": "e2e"}],
        },
        "storage": {
            "providers": [
                {
                    "service": "local",
                    "enabled": True,
                    "root_dir": str(tmp_path / "files"),
                    "folders": {
                        "inbox": "Inbox",
                        "bills": "Bills",
                        "notices": "Notices",
                        "forward_to_me": "ForwardToMe",
                        "personal": "Personal",
                        "junk": "Junk",
                        "needs_review": "NeedsReview",
                        "duplicates": "Duplicates",
                        "archive": "Archive",
                        "system": "_System",
                    },
                }
            ]
        },
        "spreadsheet": {"providers": [{"service": "none", "enabled": True}]},
        "data_protection": {"max_files_moved_per_run": 50},
        "deployment": {"dashboard_port": 5000},
    }
    return Config(data, tmp_path / "config.yaml")


def _build_fixture_providers(cfg: Config) -> Providers:
    storage_cfg = cfg.get("storage", "providers")[0]
    drive = LocalStorageProvider(root_dir=storage_cfg["root_dir"])
    folder_ids = drive.ensure_folder_structure(storage_cfg["folders"])
    return Providers(
        drive=drive,
        sheets=NoneSpreadsheetProvider(),
        llm=FixtureLLMProvider(),
        safety_agent=None,
        folder_ids=folder_ids,
        mailbox_notification_providers=[FixtureEmailProvider(FIXTURE_PDF)],
    )


@dataclass
class GateResult:
    passed: bool
    details: list[str] = field(default_factory=list)


def run_gate(tmp_path: Path) -> GateResult:
    """Run the full pipeline against the fixture and check the success scenario."""
    cfg = _build_fixture_config(tmp_path)
    providers = _build_fixture_providers(cfg)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Loopback SMTP target: any summary/alert email attempt fails fast on the
    # local machine instead of reaching a live mail server (no credentials).
    credentials = {
        "smtp": {"host": "127.0.0.1", "port": 1, "username": "", "password": ""}  # nosec B105
    }

    with patch("postmule.pipeline._build_providers", return_value=providers):
        stats = run_daily_pipeline(cfg, credentials, data_dir, dry_run=False)

    checks: list[tuple[str, bool]] = [
        ("pipeline status is not failed", stats["status"] != "failed"),
        ("one fixture email was fetched", stats["emails_found"] == 1),
        ("one PDF was OCR'd and classified", stats["pdfs_processed"] == 1),
    ]

    bills = bills_data.load_bills(data_dir)
    checks.append(("classified bill was recorded in JSON", len(bills) == 1))
    if bills:
        bill = bills[0]
        checks.append((
            "recorded bill sender matches fixture",
            bill.get("sender") == EXPECTED["sender"],
        ))
        checks.append((
            "recorded bill amount matches fixture",
            bill.get("amount_due") == EXPECTED["amount_due"],
        ))
        checks.append((
            "recorded bill is pending (visible in dashboard)",
            bill.get("status") == "pending",
        ))

    bills_dir = Path(providers.folder_ids["bills"])
    inbox_dir = Path(providers.folder_ids["inbox"])
    filed = list(bills_dir.glob("*.pdf"))
    checks.append(("fixture PDF was filed into the Bills folder", len(filed) == 1))
    if bills:
        checks.append((
            "filed PDF was renamed to the suggested filename",
            bool(filed) and filed[0].name == bills[0].get("filename"),
        ))
    checks.append(("Inbox is empty after filing", len(list(inbox_dir.glob("*.pdf"))) == 0))

    details = [f"{'PASS' if ok else 'FAIL'}: {label}" for label, ok in checks]
    return GateResult(passed=all(ok for _, ok in checks), details=details)


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = REPO_ROOT / "validation"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"e2e-fixture-{ts}.log"

    with tempfile.TemporaryDirectory() as tmp:
        result = run_gate(Path(tmp))

    lines = [f"PostMule E2E fixture gate -- {ts}", ""]
    lines.extend(result.details)
    lines.append("")
    lines.append("E2E_PASS" if result.passed else "E2E_FAIL")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {log_path}")
    print(lines[-1])
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
