# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-23 (phase=1, normal): empty backlog (owner-38/owner-39 both done), `approved/mvp-scope` present on origin, no recovery branch, both trees clean and current with origin. Ran the exact gate (`scripts/gates/gate-1-code-green.ps1` in the ops repo) — **exit 1**, red on the same two governed blockers and nothing else: `mypy.exe not clean` (ops #47) and `bandit.exe not clean` (ops #54). This run root-caused #47 precisely: `mypy.exe postmule` exits 0 standalone AND exits 0 when captured to a variable (`$out = & $exe @args 2>&1`), but exits 2 through the gate's `2>&1 | Out-Null` pipeline form under PS 5.1 — a pure pipeline artifact, mypy's real verdict is clean (89 files, no issues). bandit is deterministic: `bandit.exe -r postmule -q` exits 1 on any finding (30 Low / 0 Med / 0 High), stricter than the documented "0 Medium/High" bar, which is met. Confirmed there is no in-scope app-side fix: mypy already passes (nothing to fix), and the only non-gaming bandit fix is the governed gate edit. Regenerated `telemetry/quality-report.md` per Step 2; only diff was the timestamp, so reverted rather than push churn — substantive findings unchanged (mypy 0, bandit 30 Low / 0 Med / 0 High, coverage 75.30% over the 74% floor, 1055 passed / 2 skipped). No code edits, no queue task. 8th consecutive noop; autopilot has no in-scope move left. **Owner next (only path to unblock):** apply the two governed gate fixes from `PostMule-ops/proposals/gate-1-bandit-severity-and-exit-flake.md` (bandit `--severity-level medium`; mypy capture `$LASTEXITCODE` without the stderr-merged `Out-Null` pipe), re-pin the baseline if caged; then gate-1 passes and seeds `p2-sandbox-driver` for #96. Standing decision still open: ops #53 (automated planning stage) needs sign-off + cage re-pin.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue:** No pending owner-intake tasks remain — `owner-38` done this run, `owner-39` done last run. The next normal-mode run with an empty backlog will run the phase-1 gate script and regenerate the quality report (the gate findings live in `telemetry/quality-report.md`, not the queue). App quality state unchanged: ruff clean (postmule/), mypy 0 errors, bandit 0 Medium/High, coverage 74.29%, pytest 1055 passed.

**Blocked (needs owner action before next autopilot run can advance):**
- `p1-self-audit` (needs-owner): Complete implementation is at `ops/proposals/p1-self-audit-implementation.md` — requires owner session to apply governed files (`scripts/self-audit.ps1`, `scripts/watchdog.ps1` patch, `governance-baseline.lock` regen, `COMMANDS.md`).
- `p1-ocr-tesseract` (needs-owner): OCR per-OS Tesseract detection and clear error messaging.
- ~~pip 26.0.1 CVEs~~ RESOLVED 2026-06-22: pip upgraded to 26.1.2 in the venv and msgpack 1.2.0→1.2.1 (lock + requirements floor); `pip-audit` reports no known vulnerabilities. (The separate safe-pip.ps1-targets-global-Python issue remains, ops #11.)
- ~~Gate-1 coverage floor (align to 74%)~~ SUPERSEDED 2026-06-22 by Option B (owner-approved): two-tier gate, core (excl. web) ≥80% (met, 83%) + web ≥54% (ratchets up); implemented in `gate-1-code-green.ps1` + app pyproject. Remaining gate-1 blockers are now the bandit-severity bar (ops #54) and the `.exe` exit-flake (#47) — see `ops/proposals/gate-1-bandit-severity-and-exit-flake.md`.

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
