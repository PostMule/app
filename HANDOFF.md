# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Session 2026-06-13 (autopilot, twenty-sixth run): `approved/mvp-scope` still does not exist on origin, issue #105 still open with no labels, so per PLAN §14.16 the only phase-1 task allowed is `p1-fix-103`, already `done`. The 7 gate-1 tasks and `p1-await-mvp-scope` remain pending but not pickable. No recovery branches on origin, no new tags. Found the ops repo checked out on `review/mvp-scope-105` (2 ahead of origin) instead of `main`, holding the 18:00 and 20:00 telemetry commits from the prior two runs — pushed them to that branch and filed ops issue #6 so the owner can decide whether to merge that branch back to main. No other change since the twenty-fifth run.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Cross-platform decision (2026-06-12):** owner committed to making PostMule run on Windows and macOS, and to rewriting the harness in Python per the template. Build plan: ops `PLAN.md` §16 (two tracks: A = PostMule itself OS-agnostic, scoped by #105; B = Python harness in ops `harness/`). Track B step 1 done: `harness/` package with `config.py` + `state.py` + 16 passing tests (ruff/mypy clean). PowerShell harness in ops `scripts/` stays in production until the Python one passes gate-0 on a second OS.

**Recommended next:** Run the owner-attended MVP scoping review (#105, spec: ops PLAN §14.16) in a Fable session — now expanded to decide the OS-agnostic boundary per feature plus the macOS install/validation approach. It gates the P1 backlog and feeds the harness gate definitions; approve with the `approved/mvp-scope` tag.

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
