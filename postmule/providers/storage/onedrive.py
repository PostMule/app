"""
Microsoft OneDrive storage provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). See
postmule/providers/storage/base.py for the StorageProvider interface
this would satisfy. The registry entry is kept; configuring service:
onedrive raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "onedrive"
DISPLAY_NAME = "OneDrive"


class OneDriveProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
