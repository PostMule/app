# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-22 (phase=1, normal): empty backlog (owner-38/owner-39 both done), so I ran `gate-1-code-green.ps1` per the charter. **It exited 1 — gate-1 does NOT pass yet**, which corrects the prior entry's "every gate-1 check passes locally / should advance P1→P2" expectation. The gate reported `mypy.exe`, `bandit.exe`, `pip-audit.exe` not clean; diagnosis found one real blocker and two artifacts. **(1) bandit — the actual, deterministic blocker:** the gate runs `bandit.exe -r postmule -q`, which exits non-zero on *any* finding; the tree has 30 Low-severity findings (0 Medium, 0 High), so bandit exits 1 every run (5/5). The documented bar is "0 Medium/High" (§13.3), so the gate is stricter than the bar it enforces — the prior local verify checked the bar, not the gate's bare invocation. Verified fix: add a Medium threshold (`-ll` / `--severity-level medium`) → exit 0. **(2) mypy.exe / pip-audit.exe — intermittent exit-code flake:** both flagged non-zero in the gate run but exit 0 on direct invocation (mypy "Success: no issues found in 89 source files"; pip-audit "No known vulnerabilities found"). This is the setuptools `.exe` launcher returning a spurious code under the gate's `& $exe @args 2>&1 | Out-Null` loop — the #47 class, now also on pip-audit.exe; it makes the gate verdict non-deterministic. `quality-report.ps1` is reliable because it parses output instead of trusting the launcher exit code. **(3) deps confirmed clean:** the owner's msgpack 1.2.0→1.2.1 / pip →26.1.2 bumps hold — `pip-audit` against the venv and `requirements-lock.txt` both report no known vulnerabilities; regenerated quality report shows 0 vulns. **Net:** gate-1's substantive bars are met (mypy 0, bandit 0 Medium/High, deps 0, coverage two-tier floors pass, pytest 1055 passed) — what blocks the gate is two governed `gate-1-code-green.ps1` edits I cannot make as an autopilot run. Filed `PostMule-ops/proposals/gate-1-bandit-severity-and-exit-flake.md` with evidence and one-line fixes. I made no code edits and took no queue task; regenerated the quality report only. Both repos clean/synced; no `autopilot/recovery-*` branches. **Owner next:** apply the two gate fixes from the proposal (and re-pin the baseline if the gate is caged), then gate-1 should pass and seed `p2-sandbox-driver` for #96. Standing decision still open: ops #53 (automated planning stage) needs sign-off + cage re-pin.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue:** No pending owner-intake tasks remain — `owner-38` done this run, `owner-39` done last run. The next normal-mode run with an empty backlog will run the phase-1 gate script and regenerate the quality report (the gate findings live in `telemetry/quality-report.md`, not the queue). App quality state unchanged: ruff clean (postmule/), mypy 0 errors, bandit 0 Medium/High, coverage 74.29%, pytest 1055 passed.

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
