# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Owner session 2026-06-25 (autopilot PAUSED throughout): **ops #53 (automated planning stage) built and shipped — all six chunks.** A `pending`/`planning` task now runs as a read-only Opus plan run that writes `ops/plans/<id>.md`; the deterministic `gates.plan_gate` six-field linter verdicts it (PASS→`planned`/REVISE/ESCALATE), and a `planned` task executes as normal. Owner-confirmed fork: the plan agent writes the artifact (scoped edits) and the harness gates-then-commits it (single ops writer). Landed test-first across `state.py` (select_run_mode), `wrapper.py` (plan branch bypassing the execution postflight + bounded rounds via a `plan_attempts` counter), `cli.py` (mode selection + PLAN_* config knobs), `gates.py` (the linter), `watchdog.py` (intake seeds `stage:pending`); AUTOPILOT.md gained the `mode=plan` charter and the executor predicate moved to `stage=planned`; PLAN §17 + §14.16/§14.12/§15.1 redlines + a decisions.md entry. Chunks 2–5 ops SHAs 98460e2/d4226f4/1ffb2ef/77948fb. Cage re-pinned (chunk 6): GOVERNANCE_BASELINE→8d9e4a873662, sentinel run 28191379222 SUCCESS. Full suite 375 green, ruff + mypy clean. **Autopilot stays PAUSED** (STATE.paused=true, ops #58 open). Full detail: `PostMule-ops/BUILD-PROGRESS.md`.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**The autopilot is paused.** All four governed harness-upgrade items are now SHIPPED (#47 mypy gate fix, #57 rc-tag script, #56 Needs-owner dashboard, #53 planning stage) and the cage is re-pinned green. The remaining resume gate is the owner unpause (ops #58).

**The one remaining step (OWNER decision — ops #58):** set `STATE.paused=false` and close ops #58. This restarts the autonomous product drive, which then **self-plans #113–#122 and drives the hardening** against the rebuilt real gate. It is held back deliberately because it spends tokens and commits to main unattended — confirm before unpausing. Note before resuming: the new pipeline expects work as `stage:pending` intake tasks (owner-filed `queue` issues), which the plan run vets to `planned` before execution; the existing #113–#122 ship-blockers will flow through planning first.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
