#!/usr/bin/env bash
#
# PostMule CLI setup script for macOS/Linux - interactive or fully scripted.
#
# Sets up PostMule from a cloned repo. Run with no arguments for an interactive
# walkthrough, or pass flags for a fully silent install (CI/automation). This
# is the macOS/Linux counterpart to setup.ps1 (Windows): same venv +
# console-script install contract, no Inno Setup equivalent.
#
# Usage:
#   ./setup.sh
#
#   # Silent install (CI / automation)
#   ./setup.sh \
#     --alert-email you@example.com \
#     --gemini-api-key AIzaSy... \
#     --vpm-sender noreply@virtualpostmail.com \
#     --master-password "correct horse battery staple" \
#     --no-task-scheduler
#
# Flags:
#   --alert-email EMAIL        Email address for daily summaries and alerts.
#   --gemini-api-key KEY       Gemini API key (https://aistudio.google.com/app/api-keys)
#   --vpm-sender EMAIL         Scan notification sender (default: noreply@virtualpostmail.com)
#   --master-password PASS     Master password for encrypting credentials.
#                              If omitted in non-interactive mode, you will be
#                              prompted once; set POSTMULE_MASTER_PASSWORD to
#                              avoid the prompt entirely.
#   --no-task-scheduler        Skip registering the launchd daily job (macOS).
#   --dry-run-only             Run `postmule --dry-run` at the end but skip
#                              the launchd step. Implies --no-task-scheduler.

set -euo pipefail

MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
POSTMULE="$VENV/bin/postmule"
PYTHON_VENV="$VENV/bin/python"

ALERT_EMAIL=""
GEMINI_API_KEY=""
VPM_SENDER=""
MASTER_PASSWORD=""
NO_TASK_SCHEDULER=0
DRY_RUN_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --alert-email) ALERT_EMAIL="$2"; shift 2 ;;
    --gemini-api-key) GEMINI_API_KEY="$2"; shift 2 ;;
    --vpm-sender) VPM_SENDER="$2"; shift 2 ;;
    --master-password) MASTER_PASSWORD="$2"; shift 2 ;;
    --no-task-scheduler) NO_TASK_SCHEDULER=1; shift ;;
    --dry-run-only) DRY_RUN_ONLY=1; NO_TASK_SCHEDULER=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -n "$ALERT_EMAIL$GEMINI_API_KEY$MASTER_PASSWORD" || "$NO_TASK_SCHEDULER" -eq 1 || "$DRY_RUN_ONLY" -eq 1 ]]; then
  SILENT=1
else
  SILENT=0
fi

step()  { printf '\n==> %s\n' "$1"; }
ok()    { printf '    OK: %s\n' "$1"; }
warn()  { printf '    NOTE: %s\n' "$1"; }
fail()  { printf '\n  FAIL: %s\n\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. Check Python 3.11+
# ---------------------------------------------------------------------------
step "Checking Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+..."
PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= ($MIN_PYTHON_MAJOR, $MIN_PYTHON_MINOR) else 1)" 2>/dev/null; then
      PYTHON_BIN="$(command -v "$candidate")"
      ok "Found $("$candidate" --version 2>&1) at $PYTHON_BIN"
      break
    fi
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  fail "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required.
  macOS: brew install python@3.12
  Linux: use your distro's package manager (e.g. apt install python3.12)
Then re-run this script."
fi

# ---------------------------------------------------------------------------
# 2. Create virtual environment
# ---------------------------------------------------------------------------
step "Creating Python virtual environment..."
if [[ -d "$VENV" ]]; then
  ok "Virtual environment already exists at $VENV"
else
  "$PYTHON_BIN" -m venv "$VENV"
  ok "Created $VENV"
fi

# ---------------------------------------------------------------------------
# 3. Install PostMule
# ---------------------------------------------------------------------------
step "Installing PostMule and dependencies..."
"$PYTHON_VENV" -m pip install --upgrade pip setuptools wheel --quiet
"$PYTHON_VENV" -m pip install -e "$ROOT" --quiet
ok "postmule installed"

# ---------------------------------------------------------------------------
# 4. Copy config files
# ---------------------------------------------------------------------------
step "Setting up config files..."
CONFIG_PATH="$ROOT/config.yaml"
CREDENTIALS_PATH="$ROOT/credentials.yaml"

if [[ ! -f "$CONFIG_PATH" ]]; then
  cp "$ROOT/config.example.yaml" "$CONFIG_PATH"
  ok "Created config.yaml from template"
else
  ok "config.yaml already exists - skipping copy"
fi

if [[ ! -f "$CREDENTIALS_PATH" ]]; then
  cp "$ROOT/credentials.example.yaml" "$CREDENTIALS_PATH"
  ok "Created credentials.yaml from template"
else
  ok "credentials.yaml already exists - skipping copy"
fi

# ---------------------------------------------------------------------------
# 5. Prompt for minimum config values
# ---------------------------------------------------------------------------
step "Configuring PostMule..."

if [[ "$SILENT" -eq 0 ]]; then
  echo ""
  echo "  PostMule needs a few values to get started."
  echo "  Press Enter to skip any field (you can fill it in later)."
  echo ""
fi

# Edits config.yaml / credentials.yaml in place via a regex replace, mirroring
# setup.ps1's Set-YamlValue (preserves comments/formatting; warns if the
# pattern is not found rather than failing).
set_yaml_value() {
  local file="$1" pattern="$2" replacement="$3"
  "$PYTHON_VENV" - "$file" "$pattern" "$replacement" <<'EOF'
import re
import sys

file, pattern, replacement = sys.argv[1], sys.argv[2], sys.argv[3]
content = open(file, encoding="utf-8").read()
updated, n = re.subn(pattern, replacement, content, count=1)
if n == 0:
    print(f"    NOTE: pattern not matched in {file} - value may already be set or file format changed.")
else:
    open(file, "w", encoding="utf-8").write(updated)
EOF
}

# alert_email
if [[ -z "$ALERT_EMAIL" ]]; then
  read -r -p "  Alert email (where to send daily summaries and alerts): " ALERT_EMAIL || true
fi
if [[ -n "$ALERT_EMAIL" ]]; then
  set_yaml_value "$CONFIG_PATH" 'alert_email: ""' "alert_email: \"$ALERT_EMAIL\""
  ok "alert_email set"
else
  warn "alert_email not set - fill in config.yaml before your first real run"
fi

# scan notification sender
if [[ -z "$VPM_SENDER" ]]; then
  echo ""
  echo "  Scan notification sender: the From address on emails your virtual"
  echo "  mailbox sends when new mail arrives."
  echo "  VirtualPostMail default: noreply@virtualpostmail.com"
  read -r -p "  Scan sender [noreply@virtualpostmail.com]: " VPM_SENDER || true
  if [[ -z "$VPM_SENDER" ]]; then VPM_SENDER="noreply@virtualpostmail.com"; fi
fi
set_yaml_value "$CONFIG_PATH" 'scan_sender: "noreply@virtualpostmail.com"' "scan_sender: \"$VPM_SENDER\""
ok "scan_sender set to: $VPM_SENDER"

# Gemini API key
if [[ -z "$GEMINI_API_KEY" ]]; then
  echo ""
  echo "  Gemini API key: PostMule uses Gemini 1.5 Flash (free tier) to classify mail."
  echo "  Get a free key at: https://aistudio.google.com/app/api-keys"
  echo "  (No credit card required for the free tier)"
  read -r -p "  Gemini API key: " GEMINI_API_KEY || true
fi
if [[ -n "$GEMINI_API_KEY" ]]; then
  set_yaml_value "$CREDENTIALS_PATH" '(gemini:\n  api_key: )""' "\\1\"$GEMINI_API_KEY\""
  ok "Gemini API key set"
else
  warn "Gemini API key not set - fill in credentials.yaml before your first real run"
fi

# ---------------------------------------------------------------------------
# 6. Set master password + encrypt credentials
# ---------------------------------------------------------------------------
step "Encrypting credentials..."

if [[ -z "$MASTER_PASSWORD" && -n "${POSTMULE_MASTER_PASSWORD:-}" ]]; then
  MASTER_PASSWORD="$POSTMULE_MASTER_PASSWORD"
  ok "Using master password from POSTMULE_MASTER_PASSWORD env var"
fi
if [[ -z "$MASTER_PASSWORD" ]]; then
  echo ""
  echo "  Choose a master password to encrypt your credentials."
  echo "  This is stored in the macOS Keychain (never on disk)."
  read -r -s -p "  Master password: " MASTER_PASSWORD || true
  echo ""
fi

if [[ -n "$MASTER_PASSWORD" ]]; then
  "$PYTHON_VENV" - "$ROOT" "$CREDENTIALS_PATH" "$MASTER_PASSWORD" <<'EOF'
import sys
from pathlib import Path

root, credentials_path, master_password = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, root)
from postmule.core.credentials import save_master_password, encrypt_credentials

save_master_password(master_password)
encrypt_credentials(Path(credentials_path), Path(root) / "credentials.enc", master_password)
EOF
  ok "Credentials encrypted to credentials.enc"
  ok "Master password saved to the system keychain"
  warn "You can now delete credentials.yaml - credentials.enc is your encrypted copy"
else
  warn "Skipping encryption - run 'postmule set-master-password' and 'postmule encrypt-credentials' manually"
fi

# ---------------------------------------------------------------------------
# 7. Register the daily scheduled task (unless skipped)
# ---------------------------------------------------------------------------
if [[ "$NO_TASK_SCHEDULER" -eq 0 ]]; then
  step "Registering daily scheduled task..."
  if [[ "$(uname -s)" == "Darwin" ]]; then
    if "$POSTMULE" install-task --work-dir "$ROOT"; then
      ok "Daily launchd job registered"
    else
      warn "launchd registration failed - run 'postmule install-task' manually later"
    fi
  else
    warn "No scheduler adapter for $(uname -s) yet - skipping. Schedule 'postmule run' via cron manually."
  fi
fi

# ---------------------------------------------------------------------------
# 8. Dry run
# ---------------------------------------------------------------------------
step "Running dry-run check..."
echo "  (No files will be written, no emails sent)"
if "$POSTMULE" --dry-run; then
  ok "Dry run passed"
else
  warn "Dry run exited with errors. Review the output above before running for real."
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " PostMule setup complete"
echo "============================================================"
cat <<EOF

Next steps:
  1. Set up Google OAuth (needed for Drive + Sheets):
     Follow the instructions at: docs/install-cli.md#step-3

  2. Start the dashboard:
     $POSTMULE serve
     Then open: http://localhost:5000

  3. Run PostMule now (live run):
     $POSTMULE run
EOF
if [[ "$NO_TASK_SCHEDULER" -eq 1 ]]; then
  echo "  (Scheduled task was skipped - run '$POSTMULE install-task' to register it later)"
fi
