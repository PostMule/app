# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-14/15 (autopilot): completed `p1-stub-providers` (#105). The 14 providers marked STUB in `reviews/mvp-review.md` (imap, outlook_365, outlook_com, proton, anthropic, openai, earth_class, postscan, traveling_mailbox, airtable, excel_online, dropbox, onedrive, s3) are reduced to stub classes that keep `SERVICE_KEY`/`DISPLAY_NAME` and a registry entry but raise `NotImplementedError` on instantiation. `registry.py` now marks `imap` as `stub` (the rest already were). Removed the guarding tests for the stubbed bodies from `test_provider_completeness.py` and `test_provider_protocols.py`; replaced `test_anthropic_extended.py`/`test_openai_extended.py` with single `NotImplementedError` guard tests. Also fixed 3 pre-existing ruff findings in `test_provider_protocols.py` that the staged-file gate flagged once the file was touched. Full suite green (1005 passed, 73% coverage). This run picked up and finished WIP an earlier attempt left in `autopilot/recovery-20260614-181137` (email/llm stubs + completeness test); that branch can be disposed of.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue (rewritten per #105/council):** stub-providers done above. Next pickable task is `p1-security-core` (bump 8 vulnerable core packages, fix the 2 kept-code bandit B324 weak-hash High findings in `storage/google_drive.py`/`storage/local.py` after verifying `usedforsecurity=False`). Remaining order: E2E fixture gate → platform path layer → per-OS scheduler adapter → macOS install contract → OCR/Tesseract per-OS → platform code-audit sweep → setup wizard install-text pass → backup+ollama tests → coverage floor re-measure (last).

**Recommended (owner-attended):** Run the pre-P1 product premortem from `mvp-review.md` section 3 — a focused `council-this` session scoped to runtime/operational failure modes (cloud-LLM dependency, token cost, pipeline runtime failures), not a re-run of the 2026-04-04 architecture council. This sits beside the P1 queue, not inside it. Autopilot cannot run this (council-this spawns subagents, which the autopilot may not do).

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
