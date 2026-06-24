# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Owner session 2026-06-24 (harness upgrade, autopilot stayed PAUSED throughout): shipped 2 of the 4 governed harness items. **ops #47** — gate-1 was failing on `mypy not clean`; the prior "broken-pipe under output discard, capture fixes it" diagnosis was disproven (capture still failed the full gate). Real cause: mypy intermittently emitting `Duplicate module named "__main__"` (leading mechanism: `.mypy_cache` corruption). Fixed by invoking mypy as `-p postmule --no-incremental`; verified the full gate-1 no longer reports any tool-loop failure (only the expected owner-reserved issue-hygiene items #113–122 remain). **ops #57** — added `scripts/push-rc-tag.ps1` (the sanctioned, allowlisted path for the agent to create+push `v0.1.0-rc.N`; raw `git tag` stays denied), wired the allowlist + an AUTOPILOT.md carve-out + the p3-rc-tag seed, test-first (harness/tests/test_push_rc_tag.py, 4 pass). **ops #56** re-scoped (owner-confirmed): it targeted frozen-legacy scripts/watchdog.ps1 and an approach that conflicts with the gate-findings-as-report decision; the real fix is the Python layer (harness/watchdog.py + self_audit.py), built next session. **ops #53** (planning stage, the large build) not started — start fresh. Architecture verified: the live runner is `python -m harness run`, which spawns the agent that executes scripts/gates/*.ps1 as the product gates (so the .ps1 gate fixes are live); #56/#53 touch caged harness/*.py and need an owner cage re-pin after landing. **Autopilot stays PAUSED** (ops STATE.paused=true, ops #58 open) until the harness upgrade lands. Full session detail + the #53/#56 plan: `PostMule-ops/BUILD-PROGRESS.md`.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**The autopilot is paused. Do not resume it by running gates** — gate-1 issue-hygiene is now correctly red (9 open ship-blockers), and there is no planning stage yet, so a run would only spin red. Resume condition is in ops #58.

**Build order (owner-session, governed — the autopilot cannot self-apply these):**
1. ✅ **#47** gate-1 mypy fix (ops 8c6a695) and ✅ **#57** rc-tag push script (ops caef0f3) — both shipped + closed this session.
2. **#56** Dashboard "Needs owner" — re-scoped to the Python layer (harness/watchdog.py surfaces pending proposals for the active phase + the ≥3-noop-while-gate-red condition; harness/self_audit.py adds the same check). Drop the gate-seeded-task approach (conflicts with gate-findings-as-report). Owner-confirmed 2026-06-24. Caged — needs owner cage re-pin after landing.
3. **Planning stage #53** (the large build) — per `PostMule-ops/proposals/automated-planning-stage-and-escalation-rescope.md`. Governed/TDD in the Python harness: task lifecycle `pending→planning→planned→in-progress→done` (harness/state.py), read-only Opus `plan` run-mode (expand + premortem/critic debate + revise to bar), deterministic plan-gate linter, wiring in wrapper/classify/gates/register + AUTOPILOT.md + PLAN.md. Caged — owner cage re-pin after landing.
4. Set ops `STATE.paused=false`, close ops #58. The autopilot then **self-plans #113–#122 and drives the hardening** against the rebuilt real gate.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
