# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-21 (autopilot, mode=normal, phase=1): completed owner-intake task owner-38 (re-attempt; the prior claim ended `unknown` with no committed work — its recovery branch held only `.harness/autopilot.lock`). The harness orchestrator spawns `claude -p` headlessly; launched from inside an interactive Claude session the nested child mis-reads stdin and can tear down the operator's session (the 2026-06-21 bring-up incident). Fix (ops repo): a fail-closed guard at `provider.run_agent` (the single spawn point) keyed on `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT` — when set, no process starts and the run returns a distinct `refused-nested-session` exit, which classify maps to a hard error (deterministic, never a benign retry). Added a `doctor` `not_nested_session` check so bring-up catches it before the first supervised run, and updated BRING-UP.md to say it is now enforced, not just documented. Env read is injected so the guard/probe are deterministic under test (the suite runs with the markers set). Harness suite green (284 passed, +9), ruff + mypy clean, bandit 0 Medium/High. Governance note: edited `harness/` directly — PLAN §14.6's live governed surface excludes `harness/` Python and the Python-harness cage manifest is still a DRAFT (#29); decisions.md records that once the cage baseline is signed this change needs re-pinning (CAGE-ANCHOR Step 2). No app-repo code changes this run. No permission denials.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue:** No pending owner-intake tasks remain — `owner-38` done this run, `owner-39` done last run. The next normal-mode run with an empty backlog will run the phase-1 gate script and regenerate the quality report (the gate findings live in `telemetry/quality-report.md`, not the queue). App quality state unchanged: ruff clean (postmule/), mypy 0 errors, bandit 0 Medium/High, coverage 74.29%, pytest 1055 passed.

**Blocked (needs owner action before next autopilot run can advance):**
- `p1-self-audit` (needs-owner): Complete implementation is at `ops/proposals/p1-self-audit-implementation.md` — requires owner session to apply governed files (`scripts/self-audit.ps1`, `scripts/watchdog.ps1` patch, `governance-baseline.lock` regen, `COMMANDS.md`).
- `p1-ocr-tesseract` (needs-owner): OCR per-OS Tesseract detection and clear error messaging.
- pip 26.0.1 CVEs (3 remaining): pip cannot self-upgrade via `pip install -r requirements.txt`; deferred until safe-pip.ps1 targets the venv Python. All other runtime CVEs cleared.
- Gate-1 coverage floor: the ops gate script still requires ≥80%; proposal to align it with the measured 74% floor is at `ops/proposals/gate-1-coverage-floor.md`.

**Recommended (owner-attended):** Run the pre-P1 product premortem from `mvp-review.md` section 3 — a focused `council-this` session scoped to runtime/operational failure modes (cloud-LLM dependency, token cost, pipeline runtime failures), not a re-run of the 2026-04-04 architecture council. This sits beside the P1 queue, not inside it.

**In progress:** Live validation (#30) — PostMule installed and running at C:\Users\openclaw0123\PostMule. Dry runs pass clean. Next step: trigger a real run once a VPM scan notification email arrives.

**Other open issues (blocked or post-release):**
- #104 — Expert Directory (unblocked backlog work, not in the P1 queue; pick up post-v0.1.0 or as a gap-fill)
- #101 — setup.ps1 Gemini regex bug (superseded by the #102 wizard)
- #97 — Cloud deployment investigation (owner must decide platform/cost tradeoffs first)
- #96 — Installer validation (blocked on the macOS install contract, future P1 task)
- #93 — VPM API confirmation (requires live VPM account)
- #91 — Configure DNS for postmule.com (manual registrar step)
- #87 — Vectorize logo (requires designer/Illustrator)

**Pending (not a code task):** Push a `v*` tag (e.g. `git tag v0.1.0 && git push origin v0.1.0`) to trigger the first release. After that, update README Option A to link to the Releases page instead of "coming soon".

---

## Active Design Decisions
> Maintained in `docs/decisions.md`. Check there for the current list.
