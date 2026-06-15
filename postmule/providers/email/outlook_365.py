"""
Outlook / Microsoft 365 email provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). See
postmule/providers/email/base.py for the EmailProvider interface this
would satisfy. The registry entry is kept; configuring service:
outlook_365 raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "outlook_365"
DISPLAY_NAME = "Outlook / Microsoft 365"


class Outlook365Provider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
