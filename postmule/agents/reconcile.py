"""
Crash-recovery reconcile pass.

run_reconcile runs at pipeline start and replays the write-ahead journal left by
a crashed run (see postmule.data.journal). Each pending entry is healed
idempotently, without re-running OCR or the LLM, to reach the state the crashed
run intended: the file in its destination Drive folder and exactly one JSON
record keyed by the stable Drive file id. Reconcile only moves and renames files
that already exist on Drive (no new upload, so no MD5 step to bypass) and never
deletes or trashes a file — when a journaled file has vanished from Drive it
flags divergence for human review rather than guessing (app #115).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from postmule.data import journal, records, run_log

log = logging.getLogger("postmule.reconcile")


def empty_result() -> dict[str, Any]:
    return {
        "already_present": 0,
        "healed": 0,
        "redone": 0,
        "divergent": [],
        "needs_review": [],
        "crashed_marked": 0,
    }


def run_reconcile(
    drive: Any,
    folder_ids: dict[str, str],
    data_dir: Path,
    current_run_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Replay the journal and relabel orphaned in-progress run-log entries.

    Returns a summary of what was healed. A dry run inspects nothing and returns
    the empty result.
    """
    result = empty_result()
    if dry_run:
        return result

    result["crashed_marked"] = run_log.mark_stale_in_progress_crashed(data_dir, current_run_id)

    pending = journal.load_pending(data_dir)
    if pending:
        log.info(f"Reconcile: replaying {len(pending)} uncommitted journal entr(ies)")
    for entry in pending:
        _reconcile_entry(drive, folder_ids, data_dir, entry, result)

    if result["divergent"]:
        log.error(
            f"Reconcile: {len(result['divergent'])} journaled file(s) missing from Drive — "
            "left for manual review, no record written"
        )
    return result


def _folder_file_ids(drive: Any, folder_id: str) -> set[str]:
    if not folder_id:
        return set()
    return {f["id"] for f in drive.list_folder(folder_id)}


def _reconcile_entry(
    drive: Any,
    folder_ids: dict[str, str],
    data_dir: Path,
    entry: dict[str, Any],
    result: dict[str, Any],
) -> None:
    dfid = entry.get("drive_file_id", "")

    if entry.get("schema_version") != journal.SCHEMA_VERSION:
        log.warning(f"Reconcile: journal entry {dfid} has unknown schema_version — flagged")
        result["needs_review"].append(dfid)
        return

    # Already committed to the source of truth: drop the entry, nothing to redo.
    if records.record_exists_for_drive_file(data_dir, dfid):
        journal.commit(data_dir, dfid)
        result["already_present"] += 1
        return

    src = entry.get("src_folder_id", "")
    dest = entry.get("dest_folder_id") or folder_ids.get("needs_review", "")

    # File already in its destination: the move happened, only the record is missing.
    if dfid in _folder_file_ids(drive, dest):
        records.store_record(data_dir, entry["category"], entry["record_payload"])
        journal.commit(data_dir, dfid)
        result["healed"] += 1
        return

    # File still in the source folder: redo the move/rename, then write the record.
    if dfid in _folder_file_ids(drive, src):
        new_id = drive.move_file(dfid, dest, src) or dfid
        drive.rename_file(new_id, entry.get("suggested_filename", ""))
        records.store_record(data_dir, entry["category"], entry["record_payload"])
        journal.commit(data_dir, dfid)
        result["redone"] += 1
        return

    # File is in neither folder — externally moved/trashed. Never delete; flag it.
    result["divergent"].append(dfid)
