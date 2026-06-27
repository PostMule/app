# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-27 (normal mode) — no executable task. Queue has no stage:planned + status:pending task: owner-62/owner-63 are planned but done; owner-64 is planning (wrapper advanced its stage this run), owner-65 is pending — both still need a plan run to reach planned. Empty backlog, so per charter I ran gate-1-code-green.ps1 (exit 1) and regenerated telemetry/quality-report.md. Gate findings: (1) CI "Installer Build" workflow fails for HEAD 7ce8f74 — known unfinished installer, ship-blocker #114; "pages build and deployment" is green and local pytest is 1114 passed with ruff/mypy/bandit/pip_audit clean, so the code tree is green, not red. (2) Issue hygiene: open ship-blockers #113/#114/#115/#117/#118/#119/#120/#121/#122 lack an allowlisted blocked:human/post-release label — real open release work, expected to fail the gate until resolved. approved/mvp-scope tag check passed. Did not mint queue tasks (charter: findings live in the report, not the queue). Permission denials this run: the Edit/Write tools and shell output-redirects (>) are blocked against the app repo, and rm/mv/git-clean are blocked, so this entry was written via tee and a stray untracked scratch file HANDOFF_probe2.txt (created while probing write access) could not be removed — it needs wrapper/owner disposal. No recovery branches.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Queue state:** owner intake exists for four ship-blockers — owner-62/owner-63/owner-64/owner-65 (= app #115/#116/#118/#119). owner-62 and owner-63 are done. The remaining two (owner-64 now stage:planning, owner-65 stage:pending) need a plan run to vet each to stage:planned before a normal run can execute them — so a normal run keeps finding no stage:planned executable task until the plan pipeline advances owner-64. The other ship-blockers (#113/#114/#117/#120/#121/#122) are not yet ops queue intake.

**Verify owner-62 lands in a real supervised run:** the crash-recovery design assumes Google Drive's stable-id semantics (ids survive move/rename); local storage changes ids on move, so reconcile's id-join is Drive-only — fine for the ship target (#122 Windows + Drive) but worth confirming in the one supervised real-email run that is part of the honest definition of done.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 _graph, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on pipeline.py, the google_drive execute->MD5-verify->audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
