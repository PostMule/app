"""
Run log data layer — records the result of every PostMule run.

Schema per entry:
{
  "run_id": "uuid",
  "start_time": "YYYY-MM-DDTHH:MM:SS",
  "end_time": "YYYY-MM-DDTHH:MM:SS",
  "status": "in-progress" | "success" | "partial" | "failed" | "crashed" | "skipped",
  "emails_found": 5,
  "pdfs_processed": 5,
  "bills": 2,
  "notices": 1,
  "forward_to_me": 0,
  "junk": 1,
  "needs_review": 1,
  "errors": [],
  "api_usage": {}
}
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from postmule.data._io import atomic_write


def _run_log_file(data_dir: Path) -> Path:
    return data_dir / "run_log.json"


def load_run_log(data_dir: Path) -> list[dict[str, Any]]:
    path = _run_log_file(data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_run(data_dir: Path, entry: dict[str, Any]) -> None:
    log = load_run_log(data_dir)
    if "run_id" not in entry:
        entry["run_id"] = str(uuid.uuid4())
    log.append(entry)
    # Keep last 365 entries
    if len(log) > 365:
        log = log[-365:]
    path = _run_log_file(data_dir)
    atomic_write(path, json.dumps(log, indent=2, ensure_ascii=False))


def start_run(data_dir: Path, entry: dict[str, Any]) -> None:
    """Write an in-progress marker for a starting run so a crash leaves a trace."""
    marker = {**entry, "status": "in-progress"}
    append_run(data_dir, marker)


def finalize_run(data_dir: Path, entry: dict[str, Any]) -> None:
    """Replace the in-progress marker for entry's run_id with the final entry.

    Falls back to appending when no marker exists (e.g. a crash that never wrote
    one, or a legacy caller).
    """
    log = load_run_log(data_dir)
    run_id = entry.get("run_id")
    for i, e in enumerate(log):
        if run_id and e.get("run_id") == run_id:
            log[i] = entry
            atomic_write(_run_log_file(data_dir), json.dumps(log, indent=2, ensure_ascii=False))
            return
    append_run(data_dir, entry)


def mark_stale_in_progress_crashed(data_dir: Path, current_run_id: str) -> int:
    """Relabel orphaned in-progress entries (not the current run) as 'crashed'.

    Returns the number of entries relabelled.
    """
    log = load_run_log(data_dir)
    changed = 0
    for e in log:
        if e.get("status") == "in-progress" and e.get("run_id") != current_run_id:
            e["status"] = "crashed"
            changed += 1
    if changed:
        atomic_write(_run_log_file(data_dir), json.dumps(log, indent=2, ensure_ascii=False))
    return changed


def get_last_run(data_dir: Path) -> dict[str, Any] | None:
    log = load_run_log(data_dir)
    return log[-1] if log else None


def to_sheet_rows(run_log: list[dict[str, Any]]) -> list[list[Any]]:
    headers = [
        "Run ID",
        "Start Time",
        "End Time",
        "Status",
        "Emails Found",
        "PDFs Processed",
        "Bills",
        "Notices",
        "ForwardToMe",
        "Junk",
        "NeedsReview",
        "Errors",
    ]
    rows = [headers]
    for r in reversed(run_log):  # most recent first
        rows.append(
            [
                r.get("run_id", ""),
                r.get("start_time", ""),
                r.get("end_time", ""),
                r.get("status", ""),
                r.get("emails_found", 0),
                r.get("pdfs_processed", 0),
                r.get("bills", 0),
                r.get("notices", 0),
                r.get("forward_to_me", 0),
                r.get("junk", 0),
                r.get("needs_review", 0),
                "; ".join(r.get("errors", [])),
            ]
        )
    return rows
