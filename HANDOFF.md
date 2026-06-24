# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Owner session 2026-06-23: unblocked P1 and locked the v0.1.0 end-state plan. The two governed gate-1 blockers are fixed in ops `9f8e6db` — `bandit` now runs `--severity-level medium` (30 Low findings are within the documented 0 Medium/High bar) and ruff/mypy/bandit/pip-audit invoke via `python -m <module>` instead of the venv `.exe` shims (kills the setuptools launcher exit-code flake). Verified against the live venv; governance re-pinned. Closed ops #54, #47. Owner set the direction (decisions.md, ops 2026-06-23): ship v0.1.0 on the approved fixture scope, drive P1→P3 RC autonomously, owner tags `approved/v0.1.0` only; automated planning stage (#53) approved as a governed owner-session build. Ship premortem run (runtime/operational): v0.1.0 is safe on existing invariants; risks are post-release hardening (#110/#111/#112).

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Autonomous drive to v0.1.0 RC is unblocked.** Run the status board any time for a token-free view: `powershell -NoProfile -ExecutionPolicy Bypass -File PostMule-ops/v01-status.ps1`.

- **P1 → next empty-backlog run runs `gate-1-code-green.ps1`, which should now PASS** (all bars green: 1055 tests pass, two-tier coverage floors met, ruff/mypy/bandit/pip-audit clean, CI green, mvp-scope tag present, issues allowlisted) and seed `p2-sandbox-driver`.
- **P2 install** — autopilot builds `validation/sandbox-install.wsb` + driver, runs it in Windows Sandbox (present on this machine), emits `INSTALL_SMOKE_PASS`, closes #96. Self-driving.
- **P3 RC** — changelog/version bump, simplify pass, E2E fixture `E2E_PASS`, push `v0.1.0-rc.N`, gate-3. One gap: the agent is denied `git tag v*`, so the rc-tag push needs the owner-session fix in **ops #57** (small allowlisted script) before `p3-rc-tag` can run.
- **P4 release** — owner tags `approved/v0.1.0` on the rc commit; `harness/release.py` then releases (production-wiring review: #33).

**Owner-session work (governed — autopilot cannot self-apply):** ops #53 (automated planning stage), ops #56 (Dashboard "Needs owner" blind to an owner-blocked gate), ops #57 (rc-tag push script), #33 (release.py review).

**Post-release backlog (deferred, not blocking v0.1.0):**
- #110 — harden Gemini classification runtime failure → safe-skip, never misfile (ship premortem)
- #111 — runtime safety audit: api_safety batch/backoff + Drive mid-batch idempotency (ship premortem)
- #112 — first-run doctor self-check: scheduler / Tesseract / data-dir writable (ship premortem)
- #109 — Flask web-route integration tests (lift web coverage toward 80%)
- #108/#107/#104/#97 — E2E fixture notifier, dashboard Windows-only copy, expert personas, cloud deploy
- #30/#93 — live validation against real Gmail/VPM/Gemini/Drive (owner-credentialed, post-release)

**Blocked:human (need the owner, not the autopilot):** #96 (covered by the automated P2 sandbox run), #91 (DNS), #87 (logo vectorize).

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process). Check there for the current list.
