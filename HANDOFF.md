# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-16 (autopilot): completed `p1-macos-install-contract`. The work was preserved in recovery branch `autopilot/recovery-20260615-082236` from a prior run that was blocked by the pre-commit hook splat bug (ops #14). The hook was fixed by the owner (the `@(...)` array-force wrapper is now in place), so the committed work landed cleanly in this run. Delivered: `setup.sh` (macOS/Linux install script mirroring setup.ps1: venv + console-script install, interactive or silent config, launchd job on macOS), updated `docs/install-cli.md` and `README.md` with macOS/Linux sections, `docs/decisions.md` entry, `.gitattributes` `*.sh eol=lf` rule, and 3 tests in `tests/unit/test_setup_sh.py`. Quality state: ruff clean, mypy 0 errors, bandit 0 Medium/High, 1055 passed (3 new), coverage 74.29%.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue:** p1-macos-install-contract done. Remaining pending: p1-self-audit. Quality state as of 2026-06-16: ruff clean (postmule/), mypy 0 errors, bandit 0 Medium/High, coverage 74.29%, pytest 1055 passed.

**Blocked (needs owner action before next autopilot run can advance):**
- `p1-ocr-tesseract` (needs-owner): OCR per-OS Tesseract detection and clear error messaging.
- pip 26.0.1 CVEs (3 remaining): pip cannot self-upgrade via `pip install -r requirements.txt`; deferred until safe-pip.ps1 targets the venv Python. All other runtime CVEs cleared.
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
