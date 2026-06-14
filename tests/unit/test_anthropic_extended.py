"""Extended tests for postmule.providers.llm.anthropic (classify, _parse_response, _safe_float)."""

import json
from unittest.mock import MagicMock

import pytest

from postmule.providers.llm.anthropic import (
    AnthropicProvider,
    _parse_response,
    _safe_float,
)


class TestSafeFloat:
    def test_converts_float(self):
        assert _safe_float(3.14) == 3.14

    def test_converts_int(self):
        assert _safe_float(10) == 10.0

    def test_converts_string(self):
        assert _safe_float("42.5") == 42.5

    def test_returns_none_for_none(self):
        assert _safe_float(None) is None

    def test_returns_none_for_invalid_string(self):
        assert _safe_float("abc") is None

    def test_returns_none_for_dict(self):
        assert _safe_float({}) is None


class TestAnthropicProviderDryRun:
    def test_dry_run_returns_needs_review(self):
        provider = AnthropicProvider(api_key="test-key")
        result = provider.classify("some text", dry_run=True)
        assert result.category == "NeedsReview"
        assert result.confidence == 0.0
        assert "dry-run" in result.summary
        assert result.statement_date is None
        assert result.ach_descriptor is None


class TestGetClient:
    def test_get_client_raises_when_anthropic_not_installed(self):
        provider = AnthropicProvider(api_key="test-key")
        with pytest.raises(RuntimeError, match="anthropic is not installed"):
            provider._get_client()


class TestHealthCheck:
    def test_health_check_returns_error_when_not_installed(self):
        provider = AnthropicProvider(api_key="test-key")
        result = provider.health_check()
        assert result.ok is False
        assert result.status == "error"


class TestAnthropicClassifyWithMockedClient:
    def _make_response(self, payload, input_tokens=80, output_tokens=20):
        mock_response = MagicMock()
        mock_block = MagicMock()
        mock_block.text = json.dumps(payload)
        mock_response.content = [mock_block]
        mock_response.usage.input_tokens = input_tokens
        mock_response.usage.output_tokens = output_tokens
        return mock_response

    def test_calls_safety_agent_before_api(self):
        safety = MagicMock()
        provider = AnthropicProvider(api_key="key", safety_agent=safety)
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._make_response({
            "category": "Bill", "confidence": 0.9, "sender": "X",
            "recipients": [], "amount_due": 10.0, "due_date": None,
            "account_number": None, "summary": "test",
        })
        provider._client = mock_client

        result = provider.classify("some text")
        safety.check_and_record.assert_called_once()
        assert result.category == "Bill"

    def test_known_names_included_in_prompt(self):
        provider = AnthropicProvider(api_key="key")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._make_response({
            "category": "Bill", "confidence": 0.9, "sender": None,
            "recipients": [], "amount_due": None, "due_date": None,
            "account_number": None, "summary": "",
        })
        provider._client = mock_client

        provider.classify("text", known_names=["Alice", "Bob"])
        call_kwargs = mock_client.messages.create.call_args[1]
        prompt = call_kwargs["messages"][0]["content"]
        assert "Alice" in prompt
        assert "Bob" in prompt

    def test_additional_tokens_recorded_when_actual_exceeds_estimate(self):
        safety = MagicMock()
        provider = AnthropicProvider(api_key="key", safety_agent=safety)
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._make_response(
            {"category": "Junk", "confidence": 0.5, "sender": None,
             "recipients": [], "amount_due": None, "due_date": None,
             "account_number": None, "summary": ""},
            input_tokens=100_000, output_tokens=100_000,
        )
        provider._client = mock_client

        provider.classify("some text")
        safety.record_additional_tokens.assert_called_once()

    def test_api_error_raises_runtime_error(self):
        provider = AnthropicProvider(api_key="key")
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API down")
        provider._client = mock_client

        with pytest.raises(RuntimeError, match="Anthropic classification failed"):
            provider.classify("some text")


class TestAnthropicParseResponse:
    def test_valid_json_parsed(self):
        raw = json.dumps({
            "category": "Bill",
            "confidence": 0.95,
            "sender": "ATT",
            "recipients": ["Alice"],
            "amount_due": 94.0,
            "due_date": "2025-04-05",
            "account_number": "1234",
            "summary": "Monthly bill",
            "statement_date": "2025-03-15",
            "ach_descriptor": "ATT*PAYMENT 800-555-0100",
        })
        result = _parse_response(raw, tokens_used=100)
        assert result.category == "Bill"
        assert result.confidence == 0.95
        assert result.sender == "ATT"
        assert result.amount_due == 94.0
        assert result.statement_date == "2025-03-15"
        assert result.ach_descriptor == "ATT*PAYMENT 800-555-0100"

    def test_markdown_code_fence_stripped(self):
        body = json.dumps({
            "category": "Notice", "confidence": 0.9, "sender": "IRS",
            "recipients": [], "amount_due": None, "due_date": None,
            "account_number": None, "summary": "tax doc",
        })
        raw = f"```json\n{body}\n```"
        result = _parse_response(raw, tokens_used=50)
        assert result.category == "Notice"

    def test_invalid_json_falls_back_to_needs_review(self):
        result = _parse_response("this is not json", tokens_used=50)
        assert result.category == "NeedsReview"
        assert result.confidence == 0.0
        assert result.tokens_used == 50
        assert result.raw_response == "this is not json"

    def test_invalid_category_becomes_needs_review(self):
        raw = json.dumps({"category": "UNKNOWN", "confidence": 0.9, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        result = _parse_response(raw, tokens_used=50)
        assert result.category == "NeedsReview"

    def test_confidence_clamped_to_1(self):
        raw = json.dumps({"category": "Bill", "confidence": 5.0, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        result = _parse_response(raw, tokens_used=50)
        assert result.confidence == 1.0

    def test_confidence_clamped_to_0(self):
        raw = json.dumps({"category": "Bill", "confidence": -1.0, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        result = _parse_response(raw, tokens_used=50)
        assert result.confidence == 0.0

    def test_missing_fields_use_defaults(self):
        raw = json.dumps({"category": "Junk"})
        result = _parse_response(raw, tokens_used=10)
        assert result.category == "Junk"
        assert result.recipients == []
        assert result.amount_due is None
        assert result.statement_date is None
        assert result.ach_descriptor is None
