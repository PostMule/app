# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-17 (autopilot, gate-only run, sixth run): no queue tasks were pending. Inspected 2 new recovery branches: recovery-20260615-102435 held macos-install-contract work (setup.sh, README, docs) and recovery-20260615-160801 held wizard-install-text work (setup.html, test_setup_api.py) — both superseded by commits already on main. Ran gate-1-code-green.ps1; failed on the same 7 check categories as prior runs — no change. Regenerated ops/telemetry/quality-report.md. Gate failures: (1) coverage 74.29% vs 80% floor — proposal at ops/proposals/gate-1-coverage-floor.md; (2) ruff errors outside postmule/ — postmule/ surface clean; (3) mypy non-zero exit — 0 errors reported, likely missing type stubs; (4) bandit 30 Low findings, 0 Medium/High; (5) pip 26.0.1 CVEs (3) — blocked on p1-fix-safe-pip (needs-owner); (6) CI HEAD has one cancelled run in the 10-run window; (7) eight open issues (#30, #87, #91, #93, #96, #97, #104, #107) lack `blocked:human` or `post-release` labels.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue:** All pending queue tasks are now needs-owner; no pending tasks remain. Quality state: ruff clean (postmule/), mypy 0 errors, bandit 0 Medium/High, coverage 74.29%, pytest 1055 passed.

**Blocked (needs owner action before next autopilot run can advance):**
- `p1-self-audit` (needs-owner): Complete implementation is at `ops/proposals/p1-self-audit-implementation.md` — requires owner session to apply governed files (`scripts/self-audit.ps1`, `scripts/watchdog.ps1` patch, `governance-baseline.lock` regen, `COMMANDS.md`).
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
