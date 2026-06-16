# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-15 (autopilot): completed `p1-backup-ollama-tests` (#105). Added `TestBackupSnapshotViaPlatformPathLayer` to `tests/unit/test_backup.py` with two methods: one verifies the full `_create_zip` + `_extract_zip` round-trip using a data directory derived from `platform_paths.default_install_dir()` (monkeypatched to tmp); the other confirms ZIP arcnames never contain backslashes regardless of OS path separator. Added `TestOllamaLiveFixtureClassify` to `tests/unit/test_ollama_extended.py` with two methods that classify committed fixture OCR text (`tests/fixtures/ollama/sample_bill_ocr.txt`, a PG&E utility bill) through a real Ollama server; both skip automatically when Ollama is not running or `llama3.2` is not pulled. Also fixed pre-existing ruff issues surfaced by staging (unused `Path` and `pytest` imports, unused `restored` variable, import block order). Suite: 1048 passed, 2 skipped. Committed as `219a32d`.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue (rewritten per #105/council):** stub-providers, E2E fixture gate, platform path layer, scheduler adapter, OCR/Tesseract per-OS, platform code-audit sweep, setup wizard install-text pass, and backup+ollama tests done. `p1-security-core` is blocked — owner needs to review `PostMule-ops/proposals/safe-pip-targets-wrong-python.md` before it can be retried. `p1-macos-install-contract` is blocked on ops #14 (pre-commit hook bug); completed work preserved in recovery branches tracked by ops #18. Remaining: coverage floor re-measure (last task).

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
