# PostMule — Reference

## What PostMule Is
Open source, self-hosted automated bill management (fills the role the original Paytrust/PayMyBills once played). Processes physical mail (VPM) and email-delivered bills, AI-classifies/extracts data, manages bills, sends alerts, reconciles with bank transactions. Runs on Windows 11.

**Repo:** https://github.com/PostMule/app | **Local:** `C:\ClaudeCodeFiles\ClaudeCode\PostMule\`

## Tech Stack
| Concern | Choice |
|---|---|
| Language | Python 3.12+ |
| Scheduling | Windows Task Scheduler (configurable schedule, default 2am local) |
| OCR | pdfplumber → pytesseract (image fallback) |
| AI | Configurable LLM (default: Gemini 1.5 Flash, free tier) |
| Storage | JSON files + spreadsheet view (default: Google Sheets) |
| Dashboard | Flask + HTMX + Alpine.js (localhost:5000) |
| Encryption | Fernet (credentials) + system keyring (master password) |
| Testing | pytest, 80%+ coverage, GitHub Actions CI |

## Provider/Adapter Pattern
Every external service abstracted behind an interface (`postmule/providers/*/base.py`). Swap any provider with one config line.
Defaults: Gmail, Google Drive, Google Sheets, Gemini 1.5 Flash, VPM, YNAB.
Categories: mailbox, email (`mailbox_notifications`, `bill_intake`), storage, llm, finance, notifications, spreadsheet.

## Daily Workflow (configurable schedule, default 2am local)
1a. mailbox_notifications email → VPM notification PDFs → /Inbox
1b. bill_intake email → biller PDF attachments → /Inbox
2. Per PDF: OCR → LLM classify → rename → move → update JSON/Sheets
3. Check storage consistency
4. Pull bank transactions
5. Run bill matching → PendingBillMatches
6. Run entity discovery → propose alias matches
7. Summary email; immediate alert if ForwardToMe; proactive bill-due alert

## Cloud Storage Layout
```
PostMule/
├── _System/data/     ← JSON files, credentials.enc backup
├── Inbox/            ← unprocessed
├── Bills/ Notices/ ForwardToMe/ Personal/ Junk/ NeedsReview/
├── Duplicates/
└── Archive/
```

## Web Dashboard
- Nav: Mail (`/`), Entities, Settings, Logs, Providers
- Mail: status widget + filter tabs (All, Bills, Notices, Forward To Me, Unassigned); entity match proposals inline per item
- Providers page: category tabs + "All / Configured only" toggle
- Brand reference: `postmule/web/templates/brand_reference.html` | Living mockup: `docs/mockup_dashboard.html` (keep in sync; published at https://postmule.github.io/app/mockup_dashboard.html)

## Key Entry Points
- `postmule/pipeline.py` — `run_daily_pipeline(cfg, credentials, data_dir, dry_run)`
- `postmule/agents/backup.py` — `run_backup`, `run_restore`, `list_backups`, `get_last_backup`
- `postmule/core/constants.py` — category names, status values
- `postmule/data/_io.py` — `atomic_write`, `year_from`, `recent_years` (no domain logic)

## Dev Commands
- Venv: `.venv\` | Tests: `.venv\Scripts\pytest tests\unit\ -v`
- Issues: `gh issue list --repo PostMule/app`
