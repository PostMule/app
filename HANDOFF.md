# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-14 (autopilot, thirty-third run): `approved/mvp-scope` now exists on origin (owner approved #105 via ops PR #5, `reviews/mvp-review.md`). The six reversed/refined product decisions from the review (section 7) are recorded in `docs/decisions.md` under "MVP Scope (v0.1.0)". Per PLAN §14.16 the tag is also the P1 queue-rewrite trigger, but the rewrite needs a gate script (none exists yet — `gate-1-code-green.ps1` only seeds P2 on gate pass) to update `STATE.json` and `queue-seed.lock` together; an ad hoc `STATE.json` edit was correctly rejected by the ops pre-commit hook (§14.8). `p1-await-mvp-scope` is marked `status: blocked` in ops `STATE.json`; the seven generic `p1-gate-*` tasks are unchanged (still pending) pending the rewrite. `PostMule-ops/proposals/gate-mvp-scope-seed.md` has the drafted gate script spec and the full 10-task queue text from `mvp-review.md` section 3, ready for review/merge or an owner session.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105 — verdict approved, queue rewrite pending below; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**Recommended next:** Review and merge `PostMule-ops/proposals/gate-mvp-scope-seed.md` (or run it as an owner session) to perform the §14.16 P1 queue rewrite — mark `p1-await-mvp-scope` done, drop the seven `p1-gate-*` tasks, and seed the 10 approved tasks (E2E fixture gate → platform path layer → stub 14 untested providers → per-OS scheduler adapter → macOS install contract → OCR/Tesseract per-OS → platform code-audit sweep → setup wizard install-text pass → coverage floor re-measure → backup + ollama dedicated tests). Until that runs, the autopilot's only pickable P1 task remains `p1-fix-103` (already done), so it will noop.

**Recommended after the queue rewrite (owner-attended):** Run the pre-P1 product premortem from `mvp-review.md` section 3 — a focused `council-this` session scoped to runtime/operational failure modes (cloud-LLM dependency, token cost, pipeline runtime failures), not a re-run of the 2026-04-04 architecture council. This sits beside the P1 queue, not inside it. Autopilot cannot run this (council-this spawns subagents, which the autopilot may not do).

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
