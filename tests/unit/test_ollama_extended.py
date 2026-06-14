"""Extended tests for postmule.providers.llm.ollama (health_check, classify, _parse_response)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from postmule.providers.llm.ollama import (
    OllamaProvider,
    _parse_response,
    _safe_float,
)


class TestSafeFloat:
    def test_converts_float(self):
        assert _safe_float(3.14) == 3.14

    def test_returns_none_for_none(self):
        assert _safe_float(None) is None

    def test_returns_none_for_invalid_string(self):
        assert _safe_float("abc") is None


class TestOllamaProviderInit:
    def test_strips_trailing_slash_from_host(self):
        provider = OllamaProvider(host="http://localhost:11434/")
        assert provider.host == "http://localhost:11434"

    def test_accepts_unused_api_key(self):
        provider = OllamaProvider(api_key="ignored")
        assert provider.host == "http://localhost:11434"


class TestOllamaDryRun:
    def test_dry_run_returns_needs_review(self):
        provider = OllamaProvider()
        result = provider.classify("some text", dry_run=True)
        assert result.category == "NeedsReview"
        assert result.confidence == 0.0
        assert "dry-run" in result.summary


class TestOllamaHealthCheck:
    def test_server_unreachable(self):
        provider = OllamaProvider(host="http://localhost:11434")
        with patch("requests.get", side_effect=Exception("connection refused")):
            result = provider.health_check()
        assert result.ok is False
        assert result.status == "error"
        assert "not reachable" in result.message

    def test_model_available(self):
        provider = OllamaProvider(model="llama3.2")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "llama3.2:latest"}]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.health_check()
        assert result.ok is True
        assert result.status == "ok"
        assert "available" in result.message

    def test_model_not_available(self):
        provider = OllamaProvider(model="llama3.2")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "mistral:latest"}]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.health_check()
        assert result.ok is False
        assert result.status == "warn"
        assert "not found" in result.message
        assert "mistral" in result.message


class TestOllamaClassifyWithMockedRequests:
    def _make_response(self, payload, eval_count=50, prompt_eval_count=30):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": json.dumps(payload)},
            "eval_count": eval_count,
            "prompt_eval_count": prompt_eval_count,
        }
        return mock_resp

    def test_calls_safety_agent_and_returns_result(self):
        safety = MagicMock()
        provider = OllamaProvider(safety_agent=safety)
        mock_resp = self._make_response({
            "category": "Bill", "confidence": 0.9, "sender": "X",
            "recipients": [], "amount_due": 10.0, "due_date": None,
            "account_number": None, "summary": "test",
        })
        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = provider.classify("some text")
        safety.check_and_record.assert_called_once()
        mock_post.assert_called_once()
        assert result.category == "Bill"
        assert result.tokens_used == 80

    def test_known_names_included_in_prompt(self):
        provider = OllamaProvider()
        mock_resp = self._make_response({
            "category": "Bill", "confidence": 0.9, "sender": None,
            "recipients": [], "amount_due": None, "due_date": None,
            "account_number": None, "summary": "",
        })
        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.classify("text", known_names=["Alice", "Bob"])
        call_kwargs = mock_post.call_args[1]
        prompt = call_kwargs["json"]["messages"][0]["content"]
        assert "Alice" in prompt
        assert "Bob" in prompt

    def test_api_error_raises_runtime_error(self):
        provider = OllamaProvider()
        with patch("requests.post", side_effect=Exception("connection refused")):
            with pytest.raises(RuntimeError, match="Ollama classification failed"):
                provider.classify("some text")


class TestOllamaParseResponse:
    def test_valid_json_parsed(self):
        raw = json.dumps({
            "category": "Bill", "confidence": 0.95, "sender": "ATT",
            "recipients": ["Alice"], "amount_due": 94.0, "due_date": "2025-04-05",
            "account_number": "1234", "summary": "Monthly bill",
            "statement_date": "2025-03-15", "ach_descriptor": "ATT*PAYMENT",
        })
        result = _parse_response(raw, tokens_used=100)
        assert result.category == "Bill"
        assert result.statement_date == "2025-03-15"
        assert result.ach_descriptor == "ATT*PAYMENT"

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
        result = _parse_response("not json", tokens_used=50)
        assert result.category == "NeedsReview"
        assert result.confidence == 0.0

    def test_invalid_category_becomes_needs_review(self):
        raw = json.dumps({"category": "UNKNOWN", "confidence": 0.9, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        result = _parse_response(raw, tokens_used=50)
        assert result.category == "NeedsReview"

    def test_confidence_clamped(self):
        raw = json.dumps({"category": "Bill", "confidence": 5.0, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        assert _parse_response(raw, tokens_used=50).confidence == 1.0

        raw = json.dumps({"category": "Bill", "confidence": -1.0, "sender": None,
                           "recipients": [], "amount_due": None, "due_date": None,
                           "account_number": None, "summary": ""})
        assert _parse_response(raw, tokens_used=50).confidence == 0.0

    def test_missing_fields_use_defaults(self):
        raw = json.dumps({"category": "Junk"})
        result = _parse_response(raw, tokens_used=10)
        assert result.category == "Junk"
        assert result.recipients == []
        assert result.amount_due is None
