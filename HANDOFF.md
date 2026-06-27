# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-27 (normal mode) — owner-63 / app #116: made the LLM monthly cost cap real and on by default (commit 2409dea). `core/api_safety.py` split the dollar accounting from the daily request/token counters — `DayUsage` now carries `month` + `monthly_cost_usd`; `_maybe_reset_for_new_day` zeroes only the daily fields and a new `_maybe_reset_for_new_month` clears the monthly accumulator on a month change, so the budget is compared against month-to-date spend instead of a daily-reset counter. `check_and_record` does the budget check pre-call against the projected total and books no dollars; a new `record_cost()` books actual cost on success only, so failed calls/retries cost nothing. `providers/llm/gemini.py` takes `usd_per_1k_tokens`, passes an estimated cost to the gate and records the actual cost after a successful response; threaded through `pipeline._build_llm_provider`. Defaults changed: `monthly_cost_budget_usd` 0.00→5.00 and a new `usd_per_1k_tokens` (default 0.0) in `config.example.yaml` and the web settings route. Free-tier default (price 0.0) records $0 so the cap never false-stops it. TDD: 11 new api_safety tests + 4 gemini cost-wiring tests; full suite 1114 passed via `.venv`, coverage 76.35% (≥74% gate-1); ruff/mypy/bandit clean. State file is backward-compatible (old files load, monthly fields initialize). Closed app #116. No recovery branches, no permission denials.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Queue state:** owner intake exists for four ship-blockers — `owner-62`/`owner-63`/`owner-64`/`owner-65` (= app #115/#116/#118/#119). `owner-62` and `owner-63` are now `done`. The remaining two (`owner-64`/`owner-65`) are `stage:pending` and need a **plan run** to vet each to `stage:planned` before a normal run can execute them — so the next normal run will find no `stage:planned` task until the plan pipeline advances `owner-64`. The other ship-blockers (#113/#114/#117/#120/#121/#122) are not yet ops `queue` intake.

**Verify owner-62 lands in a real supervised run:** the crash-recovery design assumes Google Drive's stable-id semantics (ids survive move/rename); local storage changes ids on move, so reconcile's id-join is Drive-only — fine for the ship target (#122 Windows + Drive) but worth confirming in the one supervised real-email run that is part of the honest definition of done.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
