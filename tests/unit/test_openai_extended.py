"""Guarding test for the OpenAI LLM provider stub (PostMule MVP v0.1.0, #105)."""

import pytest

from postmule.providers.llm.openai import DISPLAY_NAME, OpenAIProvider


def test_instantiation_raises_not_implemented():
    with pytest.raises(NotImplementedError, match=DISPLAY_NAME):
        OpenAIProvider(api_key="dummy-key")
