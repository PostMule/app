"""Unit tests for setup wizard: API endpoints and form flow."""

from __future__ import annotations

import imaplib
import json
from unittest.mock import MagicMock, patch

import pytest
import yaml

from postmule.web.app import create_app
import postmule.web.app as _app_module


@pytest.fixture
def client(tmp_path):
    app = create_app(data_dir=tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def wizard_client(tmp_path):
    """Client with config_path and enc_path wired to tmp_path for finish-route tests."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump({"notifications": {"alert_email": ""}}), encoding="utf-8")
    enc_path = tmp_path / "credentials.enc"
    app = create_app(data_dir=tmp_path, enc_path=enc_path, config_path=config_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, tmp_path
    # Reset module globals so subsequent tests using the default `client` fixture start clean
    _app_module._config_path = None
    _app_module._enc_path = type(_app_module._enc_path)("credentials.enc")


def _post(client, url, payload):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# POST /setup/api/test-gmail
# ---------------------------------------------------------------------------

class TestTestGmail:
    def test_missing_fields_returns_error(self, client):
        r = _post(client, "/setup/api/test-gmail", {})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert data["error"]

    def test_missing_password_returns_error(self, client):
        r = _post(client, "/setup/api/test-gmail", {"gmail_address": "u@gmail.com"})
        data = r.get_json()
        assert data["ok"] is False

    def test_missing_address_returns_error(self, client):
        r = _post(client, "/setup/api/test-gmail", {"app_password": "xxxx"})
        data = r.get_json()
        assert data["ok"] is False

    def test_successful_login_returns_ok(self, client):
        mock_conn = MagicMock()
        with patch("imaplib.IMAP4_SSL", return_value=mock_conn) as mock_imap:
            r = _post(client, "/setup/api/test-gmail", {
                "gmail_address": "user@gmail.com",
                "app_password": "abcd efgh ijkl mnop",
            })
        data = r.get_json()
        assert data["ok"] is True
        assert data["error"] is None
        mock_conn.login.assert_called_once_with("user@gmail.com", "abcd efgh ijkl mnop")
        mock_conn.logout.assert_called_once()

    def test_imap_auth_failure_returns_plain_english(self, client):
        mock_conn = MagicMock()
        mock_conn.login.side_effect = imaplib.IMAP4.error(b"[AUTHENTICATIONFAILED] Invalid credentials")
        with patch("imaplib.IMAP4_SSL", return_value=mock_conn):
            r = _post(client, "/setup/api/test-gmail", {
                "gmail_address": "user@gmail.com",
                "app_password": "wrong",
            })
        data = r.get_json()
        assert data["ok"] is False
        assert "App Password" in data["error"] or "Login failed" in data["error"]

    def test_connection_error_returns_plain_english(self, client):
        with patch("imaplib.IMAP4_SSL", side_effect=OSError("Network unreachable")):
            r = _post(client, "/setup/api/test-gmail", {
                "gmail_address": "user@gmail.com",
                "app_password": "abcd efgh ijkl mnop",
            })
        data = r.get_json()
        assert data["ok"] is False
        assert "imap.gmail.com" in data["error"] or "internet" in data["error"].lower()

    def test_whitespace_trimmed_from_inputs(self, client):
        mock_conn = MagicMock()
        with patch("imaplib.IMAP4_SSL", return_value=mock_conn):
            r = _post(client, "/setup/api/test-gmail", {
                "gmail_address": "  user@gmail.com  ",
                "app_password": "  abcd efgh  ",
            })
        mock_conn.login.assert_called_once_with("user@gmail.com", "abcd efgh")


# ---------------------------------------------------------------------------
# POST /setup/api/test-gemini
# ---------------------------------------------------------------------------

class TestTestGemini:
    def test_missing_key_returns_error(self, client):
        r = _post(client, "/setup/api/test-gemini", {})
        data = r.get_json()
        assert data["ok"] is False
        assert data["error"]

    def test_empty_key_returns_error(self, client):
        r = _post(client, "/setup/api/test-gemini", {"gemini_key": "   "})
        data = r.get_json()
        assert data["ok"] is False

    def test_successful_key_returns_ok(self, client):
        with patch("postmule.web.routes.setup._probe_gemini_key", return_value=(True, None)) as mock_probe:
            r = _post(client, "/setup/api/test-gemini", {"gemini_key": "AIzaSyFake123"})
        data = r.get_json()
        assert data["ok"] is True
        assert data["error"] is None
        mock_probe.assert_called_once_with("AIzaSyFake123")

    def test_invalid_key_returns_plain_english(self, client):
        err = "Invalid API key — double-check what you copied from Google AI Studio."
        with patch("postmule.web.routes.setup._probe_gemini_key", return_value=(False, err)):
            r = _post(client, "/setup/api/test-gemini", {"gemini_key": "bad-key"})
        data = r.get_json()
        assert data["ok"] is False
        assert "key" in data["error"].lower() or "invalid" in data["error"].lower()

    def test_network_error_returns_message(self, client):
        err = "Gemini connection failed: Connection refused"
        with patch("postmule.web.routes.setup._probe_gemini_key", return_value=(False, err)):
            r = _post(client, "/setup/api/test-gemini", {"gemini_key": "AIzaSyFake123"})
        data = r.get_json()
        assert data["ok"] is False
        assert data["error"]

    def test_key_whitespace_trimmed(self, client):
        with patch("postmule.web.routes.setup._probe_gemini_key", return_value=(True, None)) as mock_probe:
            r = _post(client, "/setup/api/test-gemini", {"gemini_key": "  AIzaSyFake123  "})
        mock_probe.assert_called_once_with("AIzaSyFake123")


# ---------------------------------------------------------------------------
# Wizard form flow — step_post validation
# ---------------------------------------------------------------------------

_FULL_DATA = {
    "alert_email": "user@example.com",
    "gmail_address": "user@gmail.com",
    "app_password": "abcd efgh ijkl mnop",
    "gemini_key": "AIzaSyFake123",
    "master_password": "strongpassword",
}


def _seed_session(client, step: int, data: dict | None = None):
    with client.session_transaction() as sess:
        sess["setup_step"] = step
        sess["setup_data"] = data if data is not None else dict(_FULL_DATA)


class TestWizardStepPost:
    def test_step1_invalid_email_stays_on_step1(self, client):
        r = client.post("/setup/step/1", data={"alert_email": "notanemail"})
        assert r.status_code == 302
        assert "/setup/step/1" in r.headers["Location"]

    def test_step1_empty_email_stays_on_step1(self, client):
        r = client.post("/setup/step/1", data={"alert_email": ""})
        assert r.status_code == 302
        assert "/setup/step/1" in r.headers["Location"]

    def test_step1_valid_email_advances_to_step2(self, client):
        r = client.post("/setup/step/1", data={"alert_email": "user@example.com"})
        assert r.status_code == 302
        assert "/setup/step/2" in r.headers["Location"]

    def test_step2_missing_password_stays_on_step2(self, client):
        _seed_session(client, 2, {"alert_email": "u@e.com"})
        r = client.post("/setup/step/2", data={
            "gmail_address": "user@gmail.com",
            "app_password": "",
        })
        assert r.status_code == 302
        assert "/setup/step/2" in r.headers["Location"]

    def test_step2_invalid_gmail_stays_on_step2(self, client):
        _seed_session(client, 2, {"alert_email": "u@e.com"})
        r = client.post("/setup/step/2", data={
            "gmail_address": "notanemail",
            "app_password": "abcd efgh",
        })
        assert r.status_code == 302
        assert "/setup/step/2" in r.headers["Location"]

    def test_step2_valid_advances_to_step3(self, client):
        _seed_session(client, 2, {"alert_email": "u@e.com"})
        r = client.post("/setup/step/2", data={
            "gmail_address": "user@gmail.com",
            "app_password": "abcd efgh ijkl mnop",
        })
        assert r.status_code == 302
        assert "/setup/step/3" in r.headers["Location"]

    def test_step3_missing_key_stays_on_step3(self, client):
        _seed_session(client, 3, {**_FULL_DATA})
        r = client.post("/setup/step/3", data={"gemini_key": ""})
        assert r.status_code == 302
        assert "/setup/step/3" in r.headers["Location"]

    def test_step3_valid_key_advances_to_step4(self, client):
        _seed_session(client, 3, {**_FULL_DATA})
        r = client.post("/setup/step/3", data={"gemini_key": "AIzaSyFake123"})
        assert r.status_code == 302
        assert "/setup/step/4" in r.headers["Location"]

    def test_step4_password_mismatch_stays_on_step4(self, client):
        _seed_session(client, 4, {**_FULL_DATA})
        r = client.post("/setup/step/4", data={
            "master_password": "abc",
            "confirm_password": "xyz",
        })
        assert r.status_code == 302
        assert "/setup/step/4" in r.headers["Location"]

    def test_step4_empty_password_stays_on_step4(self, client):
        _seed_session(client, 4, {**_FULL_DATA})
        r = client.post("/setup/step/4", data={
            "master_password": "",
            "confirm_password": "",
        })
        assert r.status_code == 302
        assert "/setup/step/4" in r.headers["Location"]

    def test_step4_valid_redirects_to_finish(self, client):
        _seed_session(client, 4, {**_FULL_DATA})
        r = client.post("/setup/step/4", data={
            "master_password": "strongpassword",
            "confirm_password": "strongpassword",
        })
        assert r.status_code == 302
        assert "finish" in r.headers["Location"]

    def test_out_of_range_step_redirects_to_step1(self, client):
        r = client.get("/setup/step/99")
        assert r.status_code == 302
        assert "/setup/step/1" in r.headers["Location"]


# ---------------------------------------------------------------------------
# Wizard finish route
# ---------------------------------------------------------------------------

class TestFinishRoute:
    def test_finish_missing_session_data_redirects_to_step1(self, client):
        r = client.get("/setup/finish")
        assert r.status_code == 302
        assert "/setup/step/1" in r.headers["Location"]

    def test_finish_with_all_data_writes_config_and_redirects(self, wizard_client):
        client, tmp_path = wizard_client
        _seed_session(client, 4, dict(_FULL_DATA))

        with patch("postmule.core.credentials.encrypt_credentials") as mock_enc, \
             patch("postmule.core.credentials.save_master_password") as mock_save:
            r = client.get("/setup/finish")

        assert r.status_code == 302
        assert "setup=done" in r.headers["Location"]
        mock_save.assert_called_once_with("strongpassword")
        mock_enc.assert_called_once()

        # config.yaml should have the alert_email written
        cfg = yaml.safe_load((tmp_path / "config.yaml").read_text())
        assert cfg["notifications"]["alert_email"] == "user@example.com"

    def test_finish_cleans_up_plaintext_credentials_yaml(self, wizard_client):
        client, tmp_path = wizard_client
        _seed_session(client, 4, dict(_FULL_DATA))

        with patch("postmule.core.credentials.encrypt_credentials"), \
             patch("postmule.core.credentials.save_master_password"):
            client.get("/setup/finish")

        assert not (tmp_path / "credentials.yaml").exists()
