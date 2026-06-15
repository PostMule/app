"""
Anthropic Claude LLM provider — stub.

Not implemented in this build (PostMule MVP v0.1.0, #105). See
postmule/providers/llm/base.py for the LLMProvider interface this would
satisfy. The registry entry is kept; configuring service: anthropic
raises NotImplementedError.
"""

from __future__ import annotations

from typing import Any

SERVICE_KEY = "anthropic"
DISPLAY_NAME = "Anthropic Claude"


class AnthropicProvider:
    """Stub — not implemented in this build."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(f"{DISPLAY_NAME} is not implemented in this build")
