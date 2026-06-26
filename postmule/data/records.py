"""
Category-dispatch helpers shared by the pipeline and the reconcile pass.

A "record" is the stored dict for a single processed file. store_record routes
it to the correct per-category data layer (all of which are idempotent by
drive_file_id), and record_exists_for_drive_file answers whether a file has
already been committed to the JSON source of truth — the check reconcile uses to
decide whether a crashed run's work still needs replaying (app #115).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from postmule.data import bills as bills_data
from postmule.data import forward_to_me as ftm_data
from postmule.data import notices as notices_data
from postmule.data._io import recent_years


def store_record(data_dir: Path, category: str, record: dict[str, Any]) -> None:
    """Persist a record to the data layer for its category. Unknown categories are no-ops."""
    if category == "Bill":
        bills_data.add_bill(data_dir, record)
    elif category == "Notice":
        notices_data.add_notice(data_dir, record)
    elif category == "ForwardToMe":
        ftm_data.add_item(data_dir, record)


def record_exists_for_drive_file(data_dir: Path, drive_file_id: str) -> bool:
    """True if any bill/notice/forward-to-me record already carries this drive_file_id."""
    if not drive_file_id:
        return False
    for year in recent_years():
        bills = bills_data.load_bills(data_dir, year)
        if any(b.get("drive_file_id") == drive_file_id for b in bills):
            return True
        notices = notices_data.load_notices(data_dir, year)
        if any(n.get("drive_file_id") == drive_file_id for n in notices):
            return True
    items = ftm_data.load_forward_to_me(data_dir)
    return any(i.get("drive_file_id") == drive_file_id for i in items)
