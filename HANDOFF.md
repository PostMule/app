# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-15 (autopilot): `p1-macos-install-contract` (#105) is implemented and tested but NOT committed — blocked on a pre-commit hook bug (ops #14). The work: `setup.sh` (macOS/Linux counterpart to `setup.ps1` — venv + console-script install, interactive/silent config, credential encryption via Keychain, launchd registration on macOS via the scheduler adapter), `docs/install-cli.md` macOS/Linux quickstart + per-OS `INSTALL_CMD`/`INSTALL_SMOKE_CMD` table, `README.md` macOS/Linux quickstart block, `.gitattributes` (`*.sh` -> LF), and `tests/unit/test_setup_sh.py` (3 tests: exists, bash syntax, unknown-flag handling). Full suite green (1042 passed including the 3 new tests); `ruff check tests/unit/test_setup_sh.py` passes cleanly.

The blocker: `hooks/app/pre-commit.ps1` blocks any commit that stages exactly one `*.py` file — PowerShell collapses the single-match `Where-Object` result to a scalar string, and `& ruff check @py` then splats that string's *characters* as individual arguments (one of which is `.`), so ruff lints the entire tree and fails regardless of the staged file's actual lint status. This commit stages exactly one `.py` file (`test_setup_sh.py`), so it cannot pass. The file is governed (`governance-baseline.lock`), so autopilot cannot edit it and cannot use `--no-verify`. Filed `PostMule-ops/proposals/pre-commit-hook-splat-bug.md` (one-line fix: `$py = @($staged | Where-Object {...})`) and ops issue #14. This bug blocks *every* future commit with exactly one staged `.py` file, not just this one.

The completed work is left uncommitted in the working tree (and duplicated on `autopilot/recovery-20260615-082236`, pushed). Once the hook fix lands, the next run should commit it directly — no further implementation needed. `p1-macos-install-contract` is marked `needs-owner` in ops STATE.json (attempts=2), alongside `p1-security-core`.

Two commands were permission-denied this run while diagnosing the above: a read-only query of the git hooks-path configuration, and a checkout of four tracked files to discard local modifications (the modifications are the work described above, intentionally left in place).

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`, deferred past v0.1.0 per the MVP review). Track B step 1 (the dependency-free Python core, 55 tests) stays as already-built; the PowerShell harness in ops `scripts/` is frozen and ships v0.1.0.

**P1 queue (rewritten per #105/council):** stub-providers, E2E fixture gate, platform path layer, and scheduler adapter done. `p1-security-core` is blocked — owner needs to review `PostMule-ops/proposals/safe-pip-targets-wrong-python.md` before it can be retried. Remaining order: macOS install contract → OCR/Tesseract per-OS → platform code-audit sweep → setup wizard install-text pass → backup+ollama tests → coverage floor re-measure (last).

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
