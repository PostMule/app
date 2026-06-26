"""
Single-instance run lock for the daily pipeline.

A scheduled run and a manual run (or two scheduled runs) overlapping would
double-move files and double-count records. This lock prevents that: it is an
OS byte-range lock (``msvcrt.locking``) held on an open lock file under
``data_dir`` for the whole run. The OS releases the lock when the holding
process closes the handle or dies, so a crashed run leaves no stale lock to
detect or clean up. The lock file body records ``{pid, start_time}`` for
diagnostics only — it is not the correctness mechanism.

Windows is the ship target (app #122); ``msvcrt`` is stdlib. On a platform
without it the lock degrades to a no-op (single-host dev convenience only).
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import msvcrt

    _LOCKING: Any = msvcrt.locking
    _LK_NBLCK = msvcrt.LK_NBLCK
    _LK_UNLCK = msvcrt.LK_UNLCK
except ImportError:  # pragma: no cover - non-Windows fallback
    _LOCKING = None
    _LK_NBLCK = 0
    _LK_UNLCK = 0

log = logging.getLogger("postmule.run_lock")

_LOCK_FILENAME = "pipeline.lock"
# Lock a single byte far past any diagnostics we write at offset 0, so writing
# the {pid, start_time} body never touches the locked region.
_LOCK_OFFSET = 1 << 20


class PipelineLockHeld(RuntimeError):
    """Raised when another live process already holds the pipeline lock."""


def _lock_path(data_dir: Path) -> Path:
    return data_dir / _LOCK_FILENAME


def read_lock_info(data_dir: Path) -> dict[str, Any] | None:
    """Return the diagnostic {pid, start_time} recorded in the lock file, or None."""
    path = _lock_path(data_dir)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else None
    except (OSError, ValueError):
        return None


@contextmanager
def run_lock(data_dir: Path, *, dry_run: bool = False) -> Iterator[None]:
    """Hold the single-instance pipeline lock for the duration of the context.

    A dry run performs no writes, so it does not contend for the lock. If another
    live process holds the lock, raises PipelineLockHeld.
    """
    if dry_run or _LOCKING is None:
        yield
        return

    path = _lock_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+", encoding="utf-8")  # noqa: SIM115 - held for the lock's lifetime
    try:
        fh.seek(_LOCK_OFFSET)
        try:
            _LOCKING(fh.fileno(), _LK_NBLCK, 1)
        except OSError as exc:
            info = read_lock_info(data_dir)
            holder = (
                f" (held by pid {info.get('pid')} since {info.get('start_time')})" if info else ""
            )
            raise PipelineLockHeld(
                f"Another PostMule run already holds the pipeline lock{holder}."
            ) from exc
        try:
            fh.seek(0)
            fh.truncate()
            fh.write(
                json.dumps(
                    {"pid": os.getpid(), "start_time": datetime.now(tz=timezone.utc).isoformat()}
                )
            )
            fh.flush()
        except OSError:  # diagnostics are best-effort
            pass
        try:
            yield
        finally:
            try:
                fh.seek(_LOCK_OFFSET)
                _LOCKING(fh.fileno(), _LK_UNLCK, 1)
            except OSError:
                pass
    finally:
        fh.close()
