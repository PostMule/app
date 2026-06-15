"""
Verifies that every concrete provider class implements all methods
required by its Protocol. Catches drift when a Protocol gains a new
method that some implementations haven't added yet.

All checks are class-level (no instantiation) — no credentials required.
"""

from __future__ import annotations

import inspect

import pytest

from postmule.providers.email.base import EmailProvider

# Email
from postmule.providers.email.gmail import GmailProvider
from postmule.providers.llm.base import LLMProvider

# LLM
from postmule.providers.llm.gemini import GeminiProvider
from postmule.providers.llm.ollama import OllamaProvider
from postmule.providers.spreadsheet.base import SpreadsheetProvider

# Spreadsheet
from postmule.providers.spreadsheet.google_sheets import SheetsProvider
from postmule.providers.spreadsheet.none import NoneSpreadsheetProvider
from postmule.providers.spreadsheet.sqlite import SqliteSpreadsheetProvider
from postmule.providers.storage.base import StorageProvider

# Storage
from postmule.providers.storage.google_drive import DriveProvider
from postmule.providers.storage.local import LocalStorageProvider


def _protocol_methods(protocol) -> set[str]:
    """Return the set of public method names declared on a Protocol."""
    return {
        name
        for name, _ in inspect.getmembers(protocol, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def _assert_complete(concrete_cls, protocol) -> None:
    required = _protocol_methods(protocol)
    missing = {m for m in required if not callable(getattr(concrete_cls, m, None))}
    assert not missing, (
        f"{concrete_cls.__name__} is missing Protocol method(s): {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_PROVIDERS = [
    GmailProvider,
]


class TestEmailProviderCompleteness:
    @pytest.mark.parametrize("cls", EMAIL_PROVIDERS, ids=lambda c: c.__name__)
    def test_implements_all_protocol_methods(self, cls):
        _assert_complete(cls, EmailProvider)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

STORAGE_PROVIDERS = [
    DriveProvider,
    LocalStorageProvider,
]


class TestStorageProviderCompleteness:
    @pytest.mark.parametrize("cls", STORAGE_PROVIDERS, ids=lambda c: c.__name__)
    def test_implements_all_protocol_methods(self, cls):
        _assert_complete(cls, StorageProvider)


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

LLM_PROVIDERS = [
    GeminiProvider,
    OllamaProvider,
]


class TestLLMProviderCompleteness:
    @pytest.mark.parametrize("cls", LLM_PROVIDERS, ids=lambda c: c.__name__)
    def test_implements_all_protocol_methods(self, cls):
        _assert_complete(cls, LLMProvider)


# ---------------------------------------------------------------------------
# Spreadsheet
# ---------------------------------------------------------------------------

SPREADSHEET_PROVIDERS = [
    NoneSpreadsheetProvider,
    SheetsProvider,
    SqliteSpreadsheetProvider,
]


class TestSpreadsheetProviderCompleteness:
    @pytest.mark.parametrize("cls", SPREADSHEET_PROVIDERS, ids=lambda c: c.__name__)
    def test_implements_all_protocol_methods(self, cls):
        _assert_complete(cls, SpreadsheetProvider)
