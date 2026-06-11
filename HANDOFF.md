# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-11 (autopilot): queue had no takeable task (only `p1-await-mvp-scope`, blocked on the owner-attended #105 review), so ran `gate-1-code-green.ps1`. It failed on every check: coverage 71.43% (need 80%), ruff 374 errors, mypy 45 errors in 16 files, bandit 32 findings (4 High), pip-audit 20 known vulns across 8 packages, an issue-hygiene check on 8 open issues missing allowlisted labels, and an apparent false-positive in the CI-green check (filters all 10 recent runs instead of just HEAD's). Seeded 7 new phase-1 queue tasks (`p1-gate-coverage`, `p1-gate-ruff`, `p1-gate-mypy`, `p1-gate-bandit`, `p1-gate-pip-audit`, `p1-gate-ci-check`, `p1-gate-issue-labels`) with details in ops `STATE.json`. No code changes this run.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Recommended:** Run the owner-attended MVP scoping review (#105, spec: ops PLAN §14.16) in a Fable session. It gates the entire P1 backlog; approve its verdict table with the `approved/mvp-scope` tag. The autopilot handles everything else on schedule — owner contract is reading the pinned "Autopilot Dashboard" issue in PostMule/ops weekly.

**Previously recommended (now queued for the autopilot):** Continue #102 chunk 3 — polish and close. Remaining work: (a) test the wizard end-to-end against a real Gmail + Gemini account to confirm no edge cases, (b) close #101 (setup.ps1 Gemini regex bug — superseded by the wizard), (c) close #102 if wizard is feature-complete. Also check if step 4 (master password) needs a tester or if it's fine as-is (no external service to test).

**After #102:** Build #104 — Expert Directory. Run the bootstrapping session using `.claude/skills/Expert-framework-prompt.md`. Start with `frontend_developer` and `ux_designer`. Produces `.claude/experts/EXPERT_DIRECTORY.md`.

**In progress:** Live validation (#30) — PostMule installed and running at C:\Users\openclaw0123\PostMule. Dry runs pass clean. Next step: trigger a real run once a VPM scan notification email arrives.

**Other open issues (blocked):**
- #101 — setup.ps1 Gemini regex bug (will be closed when #102 is built)
- #97 — Cloud deployment investigation (owner must decide platform/cost tradeoffs first)
- #96 — Installer validation (unblocked once #102 is done)
- #93 — VPM API confirmation (requires live VPM account)
- #91 — Configure DNS for postmule.com (manual registrar step)
- #87 — Vectorize logo (requires designer/Illustrator)

**Pending (not a code task):** Push a `v*` tag (e.g. `git tag v0.1.0 && git push origin v0.1.0`) to trigger the first release. After that, update README Option A to link to the Releases page instead of "coming soon".

---

## Active Design Decisions
> Maintained in `docs/decisions.md`. Check there for the current list.
