"""
Write-ahead journal for the cross-system Drive-move -> JSON-store boundary.

pipeline.py moves a file on Drive and then writes its JSON record; a crash
between the two would leave a file on Drive with no record (or a double-move on a
re-run). The journal closes that window: begin() records the intended outcome of
an in-flight item, atomically, before the Drive move; commit() removes it once
the JSON record is committed. Anything left in the journal is the unfinished work
of a crashed run, which agents/reconcile.py replays idempotently (app #115).

The journal holds only in-flight items — a healthy run leaves it empty. Each
entry is one JSON file keyed by the item's stable Drive file id.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from postmule.data._io import atomic_write

log = logging.getLogger("postmule.journal")

SCHEMA_VERSION = 1


def journal_dir(data_dir: Path) -> Path:
    return data_dir / "pending" / "journal"


def _entry_path(data_dir: Path, drive_file_id: str) -> Path:
    # Key the entry file by a short stable hash of the id, never the raw id: a
    # storage backend's id can be an arbitrary-length filesystem path (local
    # storage) that would blow past the OS filename/MAX_PATH limit. The id itself
    # is preserved inside the entry body for reconcile. The hash is a filename, not
    # a security boundary.
    digest = hashlib.sha256(drive_file_id.encode("utf-8")).hexdigest()[:32]
    return journal_dir(data_dir) / f"{digest}.json"


def begin(data_dir: Path, entry: dict[str, Any]) -> Path:
    """Atomically record an in-flight item before its Drive move. Returns the entry path."""
    drive_file_id = entry["drive_file_id"]
    payload = {**entry, "schema_version": SCHEMA_VERSION, "state": "pending"}
    path = _entry_path(data_dir, drive_file_id)
    atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False))
    return path


def commit(data_dir: Path, drive_file_id: str) -> None:
    """Remove a journal entry once its JSON record is stored. No-op if absent."""
    path = _entry_path(data_dir, drive_file_id)
    if path.exists():
        path.unlink()


def load_pending(data_dir: Path) -> list[dict[str, Any]]:
    """Return all uncommitted journal entries; unreadable entries are skipped, not raised."""
    d = journal_dir(data_dir)
    if not d.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            log.warning(f"Skipping unreadable journal entry {p.name}: {exc}")
    return out
