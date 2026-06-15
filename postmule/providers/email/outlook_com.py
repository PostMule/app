"""
Outlook.com email provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). See
postmule/providers/email/base.py for the EmailProvider interface this
would satisfy. The registry entry is kept; configuring service:
outlook_com raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "outlook_com"
DISPLAY_NAME = "outlook.com / Hotmail / Live"


class OutlookComProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
