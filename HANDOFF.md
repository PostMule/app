# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-15 (autopilot): completed `p1-ocr-tesseract` (#105). `postmule/agents/ocr.py` now distinguishes `pytesseract.TesseractNotFoundError` from other extraction failures and logs a warning with per-OS install instructions (UB-Mannheim build on Windows, `brew install tesseract` on macOS, `apt install tesseract-ocr` on Linux) instead of silently swallowing it at debug level. Added `_tesseract_install_hint()` plus 4 new tests in `tests/unit/test_ocr.py` (23 total, all passing). Documented the Tesseract requirement and per-OS install commands in `docs/install-cli.md`. Also fixed pre-existing ruff violations (unused `io` import, import ordering, line-length) in `postmule/agents/ocr.py` and `tests/unit/test_ocr.py` so the commit could pass the lint gate — these were drift from the `Get-Command ruff` PATH check in the pre-commit hook being a no-op in some environments. Full suite green (1043 passed). Committed as `a05ef51` and pushed.

Checked two newer recovery branches (`autopilot/recovery-20260615-082236`, `autopilot/recovery-20260615-102435`) before starting — both hold the same already-tracked `p1-macos-install-contract` WIP (blocked on ops #14). The 102435 branch additionally has a `docs/decisions.md` entry for the macOS install contract; noted in a comment on ops issue #14 for whoever commits that work once the hook fix lands. Neither branch was cherry-picked (task is `needs-owner`, not pending).

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue (rewritten per #105/council):** stub-providers, E2E fixture gate, platform path layer, scheduler adapter, and OCR/Tesseract per-OS done. `p1-security-core` is blocked — owner needs to review `PostMule-ops/proposals/safe-pip-targets-wrong-python.md` before it can be retried. `p1-macos-install-contract` is blocked on ops #14 (pre-commit hook bug). Remaining order: platform code-audit sweep → setup wizard install-text pass → backup+ollama tests → coverage floor re-measure (last).

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
