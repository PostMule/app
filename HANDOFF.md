# PostMule — Session Handoff

**On restart, say:** "Resume PostMule work from HANDOFF.md"

---

## Last Completed
> Maintenance: before adding a new entry, delete the previous one. One issue max. Full history is in `git log`.

Autopilot run 2026-06-26 (normal mode) — STATE-integrity repair, no app code change. STATE.json showed `owner-62` as `pending/stage=planned/attempts=0`, which would have made the next normal run re-execute already-merged crash-recovery/lock work (app #115, commits 7b6a052..716c837). Cross-checking app git log, this HANDOFF, and ops commit b37a5bf (`owner-62: status=done`) confirmed owner-62 is shipped; it was wrongly rewound by the owner-38 run's end-of-run STATE write (ops 413d56f, a stale-snapshot lost update that clobbered owner-62's terminal status). Did NOT re-execute (would duplicate/conflict). Restored the permitted fields to ground truth (`status=done, attempts=1`) and filed the systemic cause as `PostMule-ops/proposals/state-lost-update-clobbers-task-status.md` (the STATE writer is governed wrapper code, not editable in-run; proposal recommends a re-read-before-write or a post-write no-regression invariant). Decision logged in `PostMule-ops/decisions.md`. App tree clean, no recovery branches, no permission denials.

---

## Next

> Check `gh issue list --repo PostMule/app` for current state before starting.
> Do not suggest or offer to work on blocked or deferred issues — only note they exist.

**Queue state:** owner intake now exists for four ship-blockers — `owner-62`/`owner-63`/`owner-64`/`owner-65` (= app #115/#116/#118/#119). `owner-62` is `done` (this run). The remaining three are `stage:pending` and need a **plan run** to vet each to `stage:planned` before a normal run can execute them — so the next normal run will find no `stage:planned` task until the plan pipeline advances `owner-63`. The other ship-blockers (#113/#114/#117/#120/#121/#122) are not yet ops `queue` intake.

**Verify owner-62 lands in a real supervised run:** the crash-recovery design assumes Google Drive's stable-id semantics (ids survive move/rename); local storage changes ids on move, so reconcile's id-join is Drive-only — fine for the ship target (#122 Windows + Drive) but worth confirming in the one supervised real-email run that is part of the honest definition of done.

**v0.1.0 ship-blockers (the autopilot's backlog once it resumes):** #113 (rebuild the tautological ship gate — keystone), #114 Tesseract bundling, #115 crash/divergence + lock, #116 cost ceiling, #117 secret/PII egress gate, #118 match-spec, #119 `_graph`, #120 Gemini consent, #121 CI/reproducible-build/coverage-gate/rollback, #122 de-scope macOS to Windows-only.

**Quality bar (from the council):** risk-based, not flat — near-100% branch coverage on `pipeline.py`, the `google_drive` execute→MD5-verify→audit/soft-delete path, and bill-matching; the gate must assert behaviours (OCR ran, MD5 verified, no auto-delete), not an aggregate number. Web UI coverage stays deferred (#109).

**Honest definition of done (corrected):** v0.1.0 also requires ONE supervised real-email run by the owner (~15 min, owner credentials + the judgment that the right file landed in Drive) — "owner only tags" was over-claimed.

**Post-release (deferred, not blocking):** #30/#93 live validation, #97/#104/#107/#108/#109 + #110/#111/#112 (the earlier premortem items, now folded into the hardening set where they overlap). **Blocked:human:** #91 DNS, #87 logo.

---

## Active Design Decisions
> Maintained in `docs/decisions.md` (product) and `PostMule-ops/decisions.md` (harness/process).
