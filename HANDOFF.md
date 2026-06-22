# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-22 (interactive, owner-attended, phase=1): cleared two gate-1 bars and advanced the autonomy design. **gate-1 progress:** (1) ruff is now clean repo-wide — the 159 findings were all in tests/scripts; applied ruff safe fixes (F401/I001) + F841 removals and relaxed E501 for `tests/**` (rationale in pyproject), full suite green at 1055 passed/2 skipped (app `5c5fb0a`); (2) open-issue label sweep done — all 9 open app issues now carry `blocked:human` (#30/#87/#91/#93/#96) or `post-release` (#97/#104/#107/#108), labels created, ops `label-allowlist.json` extended to match (ops `6ecd52f`). **Verified the E2E fixture gate runs green on demand** (`E2E_PASS`, `scripts/e2e_fixture_run.py`) — PostMule is self-testable end-to-end with no live creds. Corrected misfiled #108: the loopback-SMTP attempt is by-design (not a send risk); the real finding is that §14.18 calls the gate a "dry-run" though it runs `dry_run=False` (safety = inert providers + loopback), reclassified post-release. **Remaining gate-1 blockers (now narrow):** coverage 74.29% vs the §3 nominal 80% / configured 74% — this is P1 task 9 (re-measure the floor against the kept surface now that 16 providers are stubbed; partly an owner floor decision; `ops/proposals/gate-1-coverage-floor.md`); dependency vulns (msgpack + pip, deferred); mypy gate false-positive (direct `mypy postmule` exits 0; ops #47, tooling not code). **Design:** filed the automated-planning-stage + escalation-rescope proposal (ops `c2e4998`/`0b0288b`, tracking ops #53) — judgment automated by default (PLAN §17), owner reserved only for spend/release/taste/cage/can't-certify; three decisions locked at ≥85% (Opus plans/Sonnet executes; no human gate to public main for non-reserved; plan-gate 85%/3). Needs owner sign-off + cage re-pin to build. Tree clean, both repos synced, no `autopilot/recovery-*` branches. Owner next: the coverage-floor decision (task 9) is the main thing standing between here and gate-1 green.

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
