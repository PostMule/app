# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Owner session 2026-06-23: a 5-persona ship council overturned the earlier "v0.1.0 is safe to ship" verdict (confidences 15/32/35/45/55%). The deal-breaker: the single E2E ship gate (`scripts/e2e_fixture_run.py`) is a **tautology** — its fixture classifier returns a hardcoded amount/date ignoring the OCR text, and the gate asserts the stored value equals that same constant; it also files via LocalStorage, never the real `google_drive` MD5/audit path. Eight more blockers filed: Tesseract not bundled (#114), pipeline crash→Drive/JSON divergence + no lock (#115), LLM cost ceiling off-by-default + unreachable monthly logic (#116), secrets/PII egress to the public repo (#117), bill-match "exact date" vs 7-day-tolerance spec mismatch (#118), `_graph.py` 0% + OData injection (#119), no Gemini consent (#120), no test CI / non-reproducible build / coarse coverage gate (#121); gate rebuild is #113. Owner re-scoped (decisions.md): **Windows-only**, **fix all of #113–#121 before tag**, **autopilot-driven after the planning stage (#53) is built**. Earlier this session also fixed the P1 gate bandit/`.exe` blockers (ops 9f8e6db, closed #54/#47). **Autopilot is PAUSED** (ops STATE.paused=true, ops #58) until the harness upgrade lands.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**The autopilot is paused. Do not resume it by running gates** — gate-1 issue-hygiene is now correctly red (9 open ship-blockers), and there is no planning stage yet, so a run would only spin red. Resume condition is in ops #58.

**Build order (owner-session, governed — the autopilot cannot self-apply these):**
1. **Planning stage #53** — per `PostMule-ops/proposals/automated-planning-stage-and-escalation-rescope.md`. Governed/TDD: task lifecycle `pending→planning→planned→in-progress→done` (harness/state.py), read-only Opus `plan` run-mode that expands + runs premortem/critic debate, the deterministic plan-gate linter, wiring in wrapper/classify/gates/register + AUTOPILOT.md, re-baseline.
2. **#56** stuck-detector + Dashboard "Needs owner" fix, **#57** rc-tag push script. Autonomy is unsafe without these (the harness stalls silently — it just spun 13 noops).
3. Set ops `STATE.paused=false`, close ops #58. The autopilot then **self-plans #113–#122 and drives the hardening** against the rebuilt real gate.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
