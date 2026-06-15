"""
Excel Online spreadsheet provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). See
postmule/providers/spreadsheet/base.py for the SpreadsheetProvider
interface this would satisfy. The registry entry is kept; configuring
service: excel_online raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "excel_online"
DISPLAY_NAME = "Excel Online"


class ExcelOnlineProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
