# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-14 (autopilot, thirty-third run): `approved/mvp-scope` now exists on origin (owner approved #105 via ops PR #5, `reviews/mvp-review.md`). Per PLAN §14.16 this is the queue-rewrite trigger: `p1-await-mvp-scope` is now `done`, the seven generic `p1-gate-*` tasks are removed, and the P1 queue is replaced with the 10 tasks from `mvp-review.md` section 3 (E2E fixture gate, platform path layer, stub 14 untested providers, scheduler adapter, macOS install contract, OCR/Tesseract, platform audit sweep, wizard install-text pass, coverage re-measure, backup/ollama tests), each traceable to a KEEP row. The six reversed/refined decisions from the review (section 7) are recorded in `docs/decisions.md` under "MVP Scope (v0.1.0)". No other queue changes; ruff/mypy/bandit/pip-audit/coverage remain real gate-1 requirements and are expected to be cleaned up incidentally during the 10 tasks, re-surfacing as new gate tasks if still failing when gate-1 next runs.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105 — now resolved by the approved P1 queue below; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**Recommended next (owner-attended):** Run the pre-P1 product premortem from `mvp-review.md` section 3 — a focused `council-this` session scoped to runtime/operational failure modes (cloud-LLM dependency, token cost, pipeline runtime failures), not a re-run of the 2026-04-04 architecture council. This sits beside the P1 queue, not inside it. Autopilot cannot run this (council-this spawns subagents, which the autopilot may not do).

**P1 queue (autopilot, 10 tasks from the approved MVP scope, ops STATE.json):** E2E fixture gate script (#1, defines "done" per PLAN §14.18) → platform path layer → stub the 14 untested providers → per-OS scheduler adapter → macOS install contract → OCR/Tesseract per-OS → platform code-audit sweep → setup wizard install-text pass → coverage floor re-measure (also cleans up ruff/mypy/bandit/pip-audit across the kept surface) → backup + ollama dedicated tests.

**In progress:** Live validation (#30) — PostMule installed and running at C:\Users\openclaw0123\PostMule. Dry runs pass clean. Next step: trigger a real run once a VPM scan notification email arrives.

**Other open issues (blocked or post-release):**
- #104 — Expert Directory (unblocked backlog work, not in the P1 queue; pick up post-v0.1.0 or as a gap-fill)
- #101 — setup.ps1 Gemini regex bug (superseded by the #102 wizard)
- #97 — Cloud deployment investigation (owner must decide platform/cost tradeoffs first)
- #96 — Installer validation (blocked on the macOS install contract, P1 task 5)
- #93 — VPM API confirmation (requires live VPM account)
- #91 — Configure DNS for postmule.com (manual registrar step)
- #87 — Vectorize logo (requires designer/Illustrator)

**Pending (not a code task):** Push a `v*` tag (e.g. `git tag v0.1.0 && git push origin v0.1.0`) to trigger the first release. After that, update README Option A to link to the Releases page instead of "coming soon".

---

## Active Design Decisions
> Maintained in `docs/decisions.md`. Check there for the current list.
