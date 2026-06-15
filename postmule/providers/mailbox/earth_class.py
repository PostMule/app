"""
Earth Class Mail mailbox provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). Earth Class
Mail was also acquired by Anytime Mailbox in 2022 and no longer operates
independently. The registry entry is kept; configuring service:
earth_class raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "earth_class"
DISPLAY_NAME = "Earth Class Mail"


class EarthClassMailProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
