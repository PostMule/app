"""Tests for postmule.providers.spreadsheet.none (no-op spreadsheet provider)."""

from postmule.providers.spreadsheet.none import NoneSpreadsheetProvider


class TestNoneSpreadsheetProvider:
    def test_init_accepts_any_args(self):
        NoneSpreadsheetProvider()
        NoneSpreadsheetProvider("ignored", key="ignored")

    def test_get_or_create_workbook_returns_empty_string(self):
        provider = NoneSpreadsheetProvider()
        assert provider.get_or_create_workbook() == ""
        assert provider.get_or_create_workbook("folder-id") == ""

    def test_write_sheet_is_noop(self):
        provider = NoneSpreadsheetProvider()
        provider.write_sheet("Sheet1", [["a", "b"]])

    def test_health_check_returns_ok(self):
        provider = NoneSpreadsheetProvider()
        result = provider.health_check()
        assert result.ok is True
        assert result.status == "ok"
        assert "disabled" in result.message
