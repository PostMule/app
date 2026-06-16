"""Extended tests for postmule.providers.llm.ollama (health_check, classify, _parse_response)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from postmule.providers.llm.ollama import (
    OLLAMA_DEFAULT_HOST,
    OllamaProvider,
    _parse_response,
    _safe_float,
)

_FIXTURE_OCR = Path(__file__).parent.parent / "fixtures" / "ollama" / "sample_bill_ocr.txt"

_VALID_CATEGORIES = {"Bill", "Notice", "ForwardToMe", "Personal", "Junk", "NeedsReview"}


def _ollama_ready(host: str = OLLAMA_DEFAULT_HOST, model: str = "llama3.2") -> bool:
    """Return True only if Ollama is reachable at host and the model is pulled."""
    try:
        import requests as _req
        resp = _req.get(f"{host}/api/tags", timeout=2)
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        base = model.split(":")[0]
        return any(m.split(":")[0] == base for m in models)
    except Exception:
        return False


_requires_ollama = pytest.mark.skipif(
    not _ollama_ready(),
    reason="Ollama not running at localhost:11434 or llama3.2 not pulled",
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


# ---------------------------------------------------------------------------
# Live Ollama: structured extraction against committed fixture text
# Requires: Ollama running at localhost:11434 with llama3.2 pulled.
# Skipped automatically when those conditions are not met.
# ---------------------------------------------------------------------------

class TestOllamaLiveFixtureClassify:
    """
    Dedicated integration test: classify the committed sample bill OCR text
    through a real Ollama server and verify the result is structurally correct.
    """

    @_requires_ollama
    def test_classify_bill_fixture_returns_valid_structure(self):
        provider = OllamaProvider()
        ocr_text = _FIXTURE_OCR.read_text(encoding="utf-8")

        result = provider.classify(ocr_text, known_names=["Jane Smith"])

        assert result.category in _VALID_CATEGORIES
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.summary, str) and result.summary
        assert result.tokens_used > 0

    @_requires_ollama
    def test_classify_bill_fixture_extracts_amount_and_date(self):
        """The fixture contains $127.43 and a due date; verify Ollama extracts both."""
        provider = OllamaProvider()
        ocr_text = _FIXTURE_OCR.read_text(encoding="utf-8")

        result = provider.classify(ocr_text)

        assert result.category == "Bill"
        assert result.amount_due == pytest.approx(127.43, abs=0.01)
        assert result.due_date == "2026-04-20"
