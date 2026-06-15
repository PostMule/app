# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-15 (autopilot): attempted `p1-security-core`, marked **blocked**. Bumped `requirements.txt` floors for the 4 directly-declared vulnerable packages (cryptography>=46.0.7, Pillow>=12.2.0, requests>=2.33.0, pytest>=9.0.3) and added `requirements-lock.txt` (full freeze, all 8 pip-audit-flagged packages patched except pip). Fixed the 2 bandit B324 High findings in `storage/local.py` and `storage/google_drive.py` (`usedforsecurity=False` on MD5 integrity checksums) — verified bandit now reports 0 High. Full suite green (1005 passed, 73% coverage), mypy/ruff clean on the changed files.

Blocked on infra: `scripts/safe-pip.ps1` (ops, governed) installs into the global Python interpreter, not the app's `.venv` (`include-system-site-packages = false` makes the global install invisible to `.venv`), so `.venv`'s 7 non-pip flagged packages are still old versions and `pip-audit` against `.venv` still reports all 8. Separately, `pip` itself can't be upgraded via `pip install -r` on Windows (self-modify error), independent issue. Filed `PostMule-ops/proposals/safe-pip-targets-wrong-python.md` with both fixes. `requirements.txt`/`requirements-lock.txt` are already correct; once the proposal lands, re-running `safe-pip.ps1` should close this with no further code changes.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue (rewritten per #105/council):** stub-providers done. `p1-security-core` is blocked (see above) — owner needs to review `PostMule-ops/proposals/safe-pip-targets-wrong-python.md` before it can be retried. Remaining order after it unblocks: E2E fixture gate → platform path layer → per-OS scheduler adapter → macOS install contract → OCR/Tesseract per-OS → platform code-audit sweep → setup wizard install-text pass → backup+ollama tests → coverage floor re-measure (last).

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
