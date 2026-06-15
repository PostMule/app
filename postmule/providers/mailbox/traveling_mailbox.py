"""
Traveling Mailbox mailbox provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). No formal
mailbox Protocol exists yet; see postmule/providers/mailbox/vpm.py for
the conventions a built provider follows. The registry entry is kept;
configuring service: traveling_mailbox raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "traveling_mailbox"
DISPLAY_NAME = "Traveling Mailbox"


class TravelingMailboxProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
