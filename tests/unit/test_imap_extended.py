"""Extended tests for postmule.providers.email.imap (connection, fetch, parsing helpers)."""

import imaplib
from email.message import EmailMessage as StdEmailMessage
from unittest.mock import MagicMock, patch

import pytest

from postmule.providers.email.imap import (
    ImapProvider,
    _build_search_criteria,
    _decode_header_value,
    _fetch_single,
    _parse_date,
)


class TestBuildSearchCriteria:
    def test_unseen_only(self):
        assert _build_search_criteria("", "") == b"UNSEEN"

    def test_with_sender_filter(self):
        assert _build_search_criteria("billing@att.com", "") == b'UNSEEN FROM "billing@att.com"'

    def test_with_subject_filter(self):
        assert _build_search_criteria("", "Invoice") == b'UNSEEN SUBJECT "Invoice"'

    def test_with_both_filters(self):
        result = _build_search_criteria("att.com", "Invoice")
        assert result == b'UNSEEN FROM "att.com" SUBJECT "Invoice"'


class TestDecodeHeaderValue:
    def test_empty_string(self):
        assert _decode_header_value("") == ""

    def test_plain_ascii(self):
        assert _decode_header_value("Hello") == "Hello"

    def test_encoded_header(self):
        # "Café" encoded as UTF-8 base64 MIME word
        encoded = "=?utf-8?b?Q2Fmw6k=?="
        assert _decode_header_value(encoded) == "Café"


class TestParseDate:
    def test_empty_string(self):
        assert _parse_date("") == ""

    def test_valid_date(self):
        assert _parse_date("Thu, 01 Jan 2025 12:00:00 +0000") == "2025-01-01"

    def test_invalid_date_returns_empty(self):
        assert _parse_date("not a date") == ""


class TestImapProviderInit:
    def test_defaults(self):
        provider = ImapProvider(host="imap.example.com")
        assert provider.port == 993
        assert provider.use_ssl is True
        assert provider.processed_folder == "PostMule"
        assert provider.inbox_folder == "INBOX"


class TestConnect:
    def test_connect_ssl_success(self):
        provider = ImapProvider(host="imap.example.com", username="u", password="p")
        mock_conn = MagicMock()
        with patch("imaplib.IMAP4_SSL", return_value=mock_conn) as mock_ssl:
            conn = provider._connect()
        mock_ssl.assert_called_once_with("imap.example.com", 993)
        mock_conn.login.assert_called_once_with("u", "p")
        assert conn is mock_conn

    def test_connect_plain(self):
        provider = ImapProvider(host="imap.example.com", use_ssl=False, port=143)
        mock_conn = MagicMock()
        with patch("imaplib.IMAP4", return_value=mock_conn) as mock_plain:
            provider._connect()
        mock_plain.assert_called_once_with("imap.example.com", 143)

    def test_connect_login_failure_raises_runtime_error(self):
        provider = ImapProvider(host="imap.example.com", username="u", password="bad")
        mock_conn = MagicMock()
        mock_conn.login.side_effect = imaplib.IMAP4.error("auth failed")
        with patch("imaplib.IMAP4_SSL", return_value=mock_conn):
            with pytest.raises(RuntimeError, match="IMAP login failed"):
                provider._connect()


class TestEnsureFolderExists:
    def test_creates_folder_when_select_fails(self):
        provider = ImapProvider(host="imap.example.com")
        conn = MagicMock()
        conn.select.return_value = ("NO", [b"folder does not exist"])
        provider._ensure_folder_exists(conn, "PostMule")
        conn.create.assert_called_once_with('"PostMule"')

    def test_does_not_create_when_select_succeeds(self):
        provider = ImapProvider(host="imap.example.com")
        conn = MagicMock()
        conn.select.return_value = ("OK", [b"1"])
        provider._ensure_folder_exists(conn, "PostMule")
        conn.create.assert_not_called()


class TestHealthCheck:
    def test_ok(self):
        provider = ImapProvider(host="imap.example.com", username="u", password="p")
        mock_conn = MagicMock()
        with patch.object(provider, "_connect", return_value=mock_conn):
            result = provider.health_check()
        assert result.ok is True
        assert result.status == "ok"
        mock_conn.logout.assert_called_once()

    def test_error(self):
        provider = ImapProvider(host="imap.example.com")
        with patch.object(provider, "_connect", side_effect=RuntimeError("boom")):
            result = provider.health_check()
        assert result.ok is False
        assert result.status == "error"
        assert "boom" in result.message


class TestFetchEmails:
    def test_returns_empty_when_search_not_ok(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.uid.return_value = ("NO", [None])
        with patch.object(provider, "_connect", return_value=mock_conn):
            result = provider._fetch_emails(b"UNSEEN")
        assert result == []
        mock_conn.logout.assert_called_once()

    def test_returns_empty_when_no_results(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.uid.return_value = ("OK", [b""])
        with patch.object(provider, "_connect", return_value=mock_conn):
            result = provider._fetch_emails(b"UNSEEN")
        assert result == []

    def test_fetches_messages_for_each_uid(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.uid.return_value = ("OK", [b"1 2"])
        fake_msg = MagicMock()
        fetch_target = "postmule.providers.email.imap._fetch_single"
        with patch.object(provider, "_connect", return_value=mock_conn), \
             patch(fetch_target, return_value=fake_msg) as mock_fetch:
            result = provider._fetch_emails(b"UNSEEN")
        assert result == [fake_msg, fake_msg]
        assert mock_fetch.call_count == 2

    def test_logs_out_even_if_fetch_raises(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.uid.side_effect = [("OK", [b"1"]), Exception("boom")]
        with patch.object(provider, "_connect", return_value=mock_conn):
            result = provider._fetch_emails(b"UNSEEN")
        assert result == []
        mock_conn.logout.assert_called_once()

    def test_logout_failure_is_swallowed(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.uid.return_value = ("OK", [b""])
        mock_conn.logout.side_effect = Exception("already closed")
        with patch.object(provider, "_connect", return_value=mock_conn):
            result = provider._fetch_emails(b"UNSEEN")
        assert result == []


class TestListEmails:
    def test_list_unprocessed_emails_uses_search_criteria(self):
        provider = ImapProvider(host="imap.example.com")
        with patch.object(provider, "_fetch_emails", return_value=[]) as mock_fetch:
            provider.list_unprocessed_emails(sender_filter="att.com")
        mock_fetch.assert_called_once_with(b'UNSEEN FROM "att.com"')

    def test_list_emails_with_pdf_attachments_filters(self):
        provider = ImapProvider(host="imap.example.com")
        with_pdf = MagicMock(attachments=[{"name": "a.pdf"}])
        without_pdf = MagicMock(attachments=[])
        with patch.object(provider, "_fetch_emails", return_value=[with_pdf, without_pdf]):
            result = provider.list_emails_with_pdf_attachments()
        assert result == [with_pdf]


class TestMarkAsProcessed:
    def test_success(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.uid.return_value = ("OK", [b"1"])
        with patch.object(provider, "_connect", return_value=mock_conn):
            provider.mark_as_processed("42")
        mock_conn.expunge.assert_called_once()
        mock_conn.logout.assert_called_once()

    def test_copy_failure_returns_without_expunge(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.uid.return_value = ("NO", [None])
        with patch.object(provider, "_connect", return_value=mock_conn):
            provider.mark_as_processed("42")
        mock_conn.expunge.assert_not_called()

    def test_exception_is_logged_and_reraised(self):
        provider = ImapProvider(host="imap.example.com")
        mock_conn = MagicMock()
        mock_conn.select.side_effect = Exception("select failed")
        with patch.object(provider, "_connect", return_value=mock_conn):
            with pytest.raises(Exception, match="select failed"):
                provider.mark_as_processed("42")
        mock_conn.logout.assert_called_once()


class TestFetchSingle:
    def _make_raw_message(self, with_pdf=False, subject="Test Subject", sender="a@b.com"):
        msg = StdEmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["Date"] = "Thu, 01 Jan 2025 12:00:00 +0000"
        msg.set_content("body text")
        if with_pdf:
            msg.add_attachment(b"%PDF-1.4 fake", maintype="application",
                                subtype="pdf", filename="statement.pdf")
        return msg.as_bytes()

    def test_returns_none_when_status_not_ok(self):
        conn = MagicMock()
        conn.uid.return_value = ("NO", [None])
        assert _fetch_single(conn, b"1") is None

    def test_returns_none_when_data_empty(self):
        conn = MagicMock()
        conn.uid.return_value = ("OK", [])
        assert _fetch_single(conn, b"1") is None

    def test_parses_message_without_attachments(self):
        conn = MagicMock()
        raw = self._make_raw_message()
        conn.uid.return_value = ("OK", [(b"1 (RFC822 {123}", raw)])
        msg = _fetch_single(conn, b"1")
        assert msg is not None
        assert msg.subject == "Test Subject"
        assert msg.sender == "a@b.com"
        assert msg.received_date == "2025-01-01"
        assert msg.attachments == []

    def test_parses_message_with_pdf_attachment(self):
        conn = MagicMock()
        raw = self._make_raw_message(with_pdf=True)
        conn.uid.return_value = ("OK", [(b"1 (RFC822 {123}", raw)])
        msg = _fetch_single(conn, b"7")
        assert msg is not None
        assert len(msg.attachments) == 1
        assert msg.attachments[0]["name"] == "statement.pdf"
        assert msg.message_id == "7"

    def test_handles_non_tuple_data(self):
        conn = MagicMock()
        raw = self._make_raw_message()
        conn.uid.return_value = ("OK", [raw])
        msg = _fetch_single(conn, b"1")
        assert msg is not None
