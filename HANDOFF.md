# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-26 (normal mode, unpaused; noop_streak now 4). Backlog still empty for normal mode — both queue tasks (`owner-39`, `owner-38`) are `done` and nothing is `stage=planned`, because v0.1.0 ship-blockers #113–#122 are not yet filed as ops `queue` intake issues, so the planning pipeline has nothing to vet. Per charter Step 2 (empty backlog) I ran `gate-1-code-green.ps1`: FAIL, exit 1. Only finding is the missing-label bar — open issues #113–#122 lack the allowlisted `blocked:human`/`post-release` label (owner-reserved labeling, the only thing that clears this gate short of closing them). Local quality green: 1055 passed / 2 skipped, coverage 75.30% (≥74%), ruff + mypy + bandit clean. Regenerated `PostMule-ops/telemetry/quality-report.md`. No queue tasks minted (charter: gate exit code enforces the bars; no per-check tasks). No app code changed. Clean tree, no recovery branches. No permission denials this run. This is the 4th consecutive noop — every run will repeat until the owner either files #113–#122 as ops `queue` intake or labels them.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**The autopilot is UNPAUSED** (owner did this in ops `9e9505e`). All four governed harness-upgrade items shipped (#47, #57, #56, #53) and the cage is re-pinned green. The autonomous product drive is now live but has nothing to drive: the ops queue holds no `stage=planned` (or `pending`) work.

**The one remaining OWNER step to start the v0.1.0 drive:** file ship-blockers #113–#122 as ops `queue`-labeled intake issues (the watchdog seeds them `stage:pending`, the plan run vets each to `planned`, then a normal run executes). Until they exist as ops intake, every run sees an empty backlog and just re-runs the gate. Gate-1 will stay red until (a) #121 builds a real code-CI workflow that produces a green run for HEAD — today only `pages-build-deployment` runs — and (b) #113–#122 are closed or carry the `blocked:human`/`post-release` label.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
