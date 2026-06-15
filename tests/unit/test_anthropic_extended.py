"""Guarding test for the Anthropic LLM provider stub (PostMule MVP v0.1.0, #105)."""

import pytest

from postmule.providers.llm.anthropic import DISPLAY_NAME, AnthropicProvider


def test_instantiation_raises_not_implemented():
    with pytest.raises(NotImplementedError, match=DISPLAY_NAME):
        AnthropicProvider(api_key="dummy-key")
