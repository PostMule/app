# CLI Install Guide

For advanced users who prefer the command line. If you want a guided setup wizard, use the [Windows installer](https://github.com/PostMule/app/releases) instead. macOS and Linux do not have a graphical installer — use `setup.sh` below.

## Quickest path — setup script (Windows)

After cloning the repo, run:

```powershell
.\setup.ps1
```

This handles Steps 1–2 and 4–5 below automatically (interactive prompts for email, API key, and master password). For a fully silent install:

```powershell
.\setup.ps1 `
  -AlertEmail you@example.com `
  -ImapHost imap.gmail.com `
  -ImapUsername your@gmail.com `
  -ImapPassword "your-app-password" `
  -GeminiApiKey AIzaSy... `
  -MasterPassword "your master password" `
  -NoTaskScheduler
```

## Quickest path — setup script (macOS / Linux)

After cloning the repo, run:

```bash
./setup.sh
```

This is the macOS/Linux counterpart to `setup.ps1` — same venv + console-script
install, interactive prompts for email, API key, and master password (stored in
the macOS Keychain via `keyring`). On macOS it also registers a `launchd` daily
job (the Linux equivalent is not yet automated — schedule `postmule run` via
`cron` manually). For a fully silent install:

```bash
./setup.sh \
  --alert-email you@example.com \
  --gemini-api-key AIzaSy... \
  --vpm-sender noreply@virtualpostmail.com \
  --master-password "your master password" \
  --no-task-scheduler
```

The manual steps below are for reference or if you prefer to run each step yourself.

## Requirements

- Python 3.11+ (Windows, macOS, or Linux)
- A virtual mailbox service (VirtualPostMail, Earth Class Mail, Traveling Mailbox, PostScan)
- An email account accessible via IMAP (Gmail, Outlook, or any IMAP server)
  - Gmail users: generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- An API key for a supported LLM (default: Gemini 1.5 Flash — free tier)

**No Google Cloud Console setup required.** PostMule defaults to local file storage and IMAP email — no OAuth, no Drive API, no Sheets API. Google integrations are available as opt-in providers if you want cloud storage.

## Step 1 — Clone and install

Windows:
```powershell
git clone https://github.com/PostMule/app.git PostMule
cd PostMule
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

macOS / Linux:
```bash
git clone https://github.com/PostMule/app.git PostMule
cd PostMule
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Step 2 — Create config files

```powershell
copy config.example.yaml config.yaml
copy credentials.example.yaml credentials.yaml
```

Both files are in `.gitignore` and will never be committed.

Edit `config.yaml`:
- Set `notifications.alert_email` to where you want alerts sent
- Set `email.providers[0].address` and `.host` for your IMAP account
- Set `mailbox.providers[0].service` to your virtual mailbox provider

Edit `credentials.yaml`:
- Set `accounts.main.username` and `.password` (your IMAP login / app password)
- Set `gemini.api_key` (get one free at [aistudio.google.com](https://aistudio.google.com))

See [Configuration Reference](configuration.md) for all available fields.

## Step 3 — Encrypt credentials

```
postmule set-master-password
postmule encrypt-credentials
```

Your master password is stored in the system keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service). After encrypting, you can delete `credentials.yaml`.

## Step 4 — Test and schedule

```
# Test with a dry run (no writes, no emails)
postmule --dry-run

# Schedule the daily run (time set in config.yaml → schedule.run_time)
# Windows: Task Scheduler. macOS: launchd. Linux: not yet automated — use cron.
postmule install-task

# Run immediately
postmule run
```

## First-Run Checklist

- `postmule --dry-run` completes without errors
- Dashboard loads at [localhost:5000](http://localhost:5000)
- Storage folders created under the per-OS data directory (`C:\ProgramData\PostMule\files\` on Windows, `~/Library/Application Support/PostMule/files/` on macOS, or your configured `root_dir`)
- Test email received at your `alert_email`
- Windows: task visible in Task Scheduler. macOS: job visible via `launchctl list | grep postmule`.

## Optional: Google Cloud setup

If you want Google Drive storage or Google Sheets view instead of local defaults:

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable the **Google Drive API** and/or **Google Sheets API**
3. Create an OAuth 2.0 Client ID (Desktop app type)
4. Run `postmule connect-google` to complete the OAuth consent flow
5. In `config.yaml`, change `storage.providers[0].service` to `google_drive` and/or `spreadsheet.providers[0].service` to `google_sheets`

## Install contract (per-OS)

These are the canonical install and smoke-test commands for automated validation
(CI, sandbox/clean-deps install gates). No Inno Setup equivalent exists for
macOS/Linux — `setup.sh` (venv + console-script) is the only supported path there.

| OS            | `INSTALL_CMD`  | `INSTALL_SMOKE_CMD` |
|---------------|----------------|---------------------|
| Windows       | `.\setup.ps1 -NoTaskScheduler -MasterPassword <pw>` | `.venv\Scripts\postmule.exe --version` then `.venv\Scripts\postmule.exe --dry-run` against committed fixtures |
| macOS / Linux | `./setup.sh --no-task-scheduler --master-password <pw>` | `.venv/bin/postmule --version` then `.venv/bin/postmule --dry-run` against committed fixtures |

Both scripts are idempotent (re-running skips steps that already succeeded) and
exit non-zero on failure, so `INSTALL_CMD` followed by `INSTALL_SMOKE_CMD` is a
complete pass/fail check of a fresh install.
