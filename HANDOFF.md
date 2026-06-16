# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-16 (autopilot): attempted `p1-fix-safe-pip` (ops #11). The primary deliverable — editing `ops/scripts/safe-pip.ps1` to target the project `.venv` instead of the global Python — is blocked: `safe-pip.ps1` is in the governed surface (`governance-baseline.lock`), and the pre-commit hook rejects any commit that changes it. The proposal was filed in the prior run (`ops/proposals/safe-pip-targets-wrong-python.md`). The app-side deliverable was completed: three tests in `tests/unit/test_venv_integrity.py` verify the pytest process runs inside `.venv` and that key packages are installed there (1052 passed, 74.29% coverage). Task marked needs-owner. Decision log updated in `docs/decisions.md`.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue complete.** All tasks are done or needs-owner. Quality state as of 2026-06-15: ruff clean, mypy clean, bandit 0 Medium/0 High, coverage 74%, pytest 1049 passed.

**Blocked (needs owner action before next autopilot run can advance):**
- `p1-security-core` (needs-owner): pip-audit still reports 21 CVEs in the venv because `safe-pip.ps1` installs to the global Python instead of `.venv`. The proposal to fix safe-pip is at `ops/proposals/safe-pip-targets-wrong-python.md`. Once fixed, re-run safe-pip with requirements-lock.txt (already has patched pins) and re-run pip-audit.
- `p1-macos-install-contract` (needs-owner, attempts=2): work complete (setup.sh, docs, tests) but blocked on pre-commit hook bug (ops #14, proposals/pre-commit-hook-splat-bug.md). Completed work preserved in recovery branches tracked by ops #18.
- `p1-ocr-tesseract` (needs-owner): OCR per-OS Tesseract detection and clear error messaging.
- Gate-1 coverage floor: the ops gate script still requires ≥80%; proposal to align it with the measured 74% floor is at `ops/proposals/gate-1-coverage-floor.md`.

**Recommended (owner-attended):** Run the pre-P1 product premortem from `mvp-review.md` section 3 — a focused `council-this` session scoped to runtime/operational failure modes (cloud-LLM dependency, token cost, pipeline runtime failures), not a re-run of the 2026-04-04 architecture council. This sits beside the P1 queue, not inside it.

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
