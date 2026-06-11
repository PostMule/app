# PostMule Autopilot — Deployment Harness Design (v2)

> Status: DRAFT v2 — full specification, awaiting owner approval (session 2026-06-10).
> Supersedes v1 (charter-level sketch). This version specifies the phase state machine,
> gate mechanics, recovery procedures, schemas, and release verification in full.

---

## 1. Core principles

1. **Deterministic scripts gate; the LLM never grades its own homework.**
   Every phase transition is decided by a pure-PowerShell gate script (zero tokens) that
   runs verifiable checks. The LLM does the *work*; scripts do the *judging*. The LLM is
   not permitted (and not trusted) to advance the phase field.
2. **Tags are evidence; re-verification is mandatory.**
   Gate passes are recorded as annotated git tags, but the release script re-runs every
   gate fresh at release time. A stale green tag can never ship a broken build.
3. **Git is the only state store.** Phase state, run history summaries, and human handoff
   all live in committed files. A run killed at any instant loses at most one uncommitted
   chunk, which the next run's recovery procedure preserves on a branch.
4. **Fail fast, fail cheap, retry on schedule.** Token exhaustion is an expected, normal
   outcome — not an error. Every run is bounded (one chunk, hard timeout); the scheduler
   provides the retry loop aligned to Pro's 5-hour usage windows.
5. **Self-protection over persistence.** Repeated failure pauses the system and notifies
   the owner rather than burning tokens on a loop it cannot escape.

---

## 2. File layout

```
.claude/autopilot/
├── PLAN.md                  # this design (committed)
├── AUTOPILOT.md             # run charter — the prompt every headless run executes (committed)
├── STATE.json               # phase + task queue + counters (committed; see §6)
├── RUNS.jsonl               # append-only run telemetry (gitignored, local)
├── STOP                     # kill switch — if this file exists, runs exit immediately
├── scripts/
│   ├── run-autopilot.ps1    # wrapper: lock → preflight → claude -p → postflight (§4)
│   ├── recover.ps1          # deterministic crash recovery (§5.2)
│   ├── watchdog.ps1         # daily liveness check, zero tokens (§5.6)
│   ├── register-tasks.ps1   # schtasks registration for autopilot + watchdog
│   ├── release.ps1          # the only path to a v* tag (§8)
│   └── gates/
│       ├── gate-0-bootstrap.ps1
│       ├── gate-1-code-green.ps1
│       ├── gate-2-install.ps1
│       └── gate-3-rc.ps1
└── logs/                    # full claude -p transcripts (gitignored)
```

---

## 3. Phase state machine

```
P0 Bootstrap → P1 Code Green → P2 Install Validated → P3 Release Candidate
     → [OWNER APPROVAL] → P4 Released → P5 Live Validated (owner-triggered) → P6 Maintenance
```

**What moves a phase forward:** running `gates/gate-N-*.ps1`. On pass, the script (not the
LLM) does three things atomically: sets `phase` in STATE.json, commits with message
`gate: pN passed — <summary>`, and pushes annotated tag `gate/pN-<name>`. On fail, it
prints the failing checks and exits 1; phase is untouched. The autopilot's charter says:
"when you believe the current phase's backlog is empty, run the gate script; its exit code
is the answer."

| Phase | Exit gate | Machine-verified criteria (all must pass) | Tag written |
|---|---|---|---|
| **P0 Bootstrap** | gate-0 | All harness files exist; `schtasks /query` shows both tasks; ≥1 RUNS.jsonl record with `outcome=success`; STOP absent | `gate/p0-bootstrap` |
| **P1 Code Green** | gate-1 | Full pytest suite green; coverage ≥80%; `gh run list --branch main -L1` = success (CI agrees); zero open issues lacking both `blocked:human` and `post-release` labels; working tree clean and synced with origin | `gate/p1-code-green` |
| **P2 Install Validated** | gate-2 | Sandbox evidence log exists at `validation/sandbox-install-<ts>.log` containing the `INSTALL_SMOKE_PASS` marker; SHA-256 of `setup.ps1` recorded in that log equals current `setup.ps1` hash (evidence isn't stale); #96 closed with the log attached | `gate/p2-install` |
| **P3 Release Candidate** | gate-3 | `CHANGELOG.md` has a `v0.1.0` section; version bumped in `pyproject.toml`; README release section ready; tag `v0.1.0-rc.N` pushed; CI build workflow for that rc tag succeeded and produced artifacts | `gate/p3-rc` |
| **P4 Released** | release.ps1 only (§8) | All of gates 1–3 **re-run fresh and pass** + owner approval tag exists | `v0.1.0` + `gate/p4-released` |
| **P5 Live Validated** | owner-triggered checklist | One real pipeline run against live Gmail/VPM/Gemini/Drive succeeds (#30, #93); evidence log committed | `gate/p5-live` |
| **P6 Maintenance** | — (terminal) | Cadence drops to daily; runs only triage new issues and CI failures | — |

**Owner approval gate (P3→P4):** the only human action in the critical path. The
autopilot files a "Release approval requested: v0.1.0" issue containing the staged
one-liner. Owner either runs it, or tells Claude "approved" in an interactive session:

```powershell
git tag -a approved/v0.1.0 -m "Release approved by owner"; git push origin approved/v0.1.0
```

`release.ps1` refuses to run without `approved/v0.1.0` reachable on origin. The autopilot
charter forbids creating any `approved/*` or `v*` tag itself — and because gate evidence
is re-verified by `release.ps1`, even a misbehaving run cannot ship by lying about state.

**Phase regression:** phases never decrement. If main breaks in a later phase, the run
enters doctor mode (§5.3) until green again; the re-verification rule (principle 2) makes
stale gate tags harmless.

---

## 4. Run lifecycle (`run-autopilot.ps1`)

Every scheduled run, in order:

1. **Kill switch** — if `STOP` exists, append a `skipped` record and exit 0.
2. **Lock** — create `logs/.lock` containing PID + ISO timestamp. If a lock already
   exists: if its PID is alive, exit (overlap); if dead, this is a crashed run →
   invoke `recover.ps1` (§5.2), then continue.
3. **Pause check** — if `STATE.json .paused == true`, exit (watchdog/owner unpauses).
4. **Sync** — `git fetch`; if local main diverged from origin, recover.ps1 then hard-sync.
5. **Preflight health probe** — fast suite: `pytest tests/unit -q -x --tb=no` (~zero
   tokens). Green → `mode=normal`. Red → `mode=doctor` (§5.3).
6. **Invoke the agent** —
   `claude -p (Get-Content AUTOPILOT.md -Raw) --model sonnet --fallback-model haiku
   --permission-mode acceptEdits` with output teed to `logs/run-<ts>.log`,
   hard timeout 90 minutes (kill on expiry; next run recovers).
7. **Postflight (deterministic)** — verify: working tree clean, branch pushed, HANDOFF.md
   modified this run. Any violation → `recover.ps1` (preserve work, restore clean main).
8. **Record** — classify outcome from exit code + log tail
   (`success | rate_limited | timeout | error | noop`), append to RUNS.jsonl, update
   `STATE.json .last_run`, increment/reset failure counters, release lock.

**The charter (AUTOPILOT.md) instructs the agent to:**
- Read STATE.json; in doctor mode, work only on restoring green (fix or revert).
- In normal mode, take the **first** queue task for the current phase with
  `status=pending` and `attempts<2`; increment `attempts` and commit *before* starting
  work (so a crash mid-task still counts the attempt).
- One task per run. TDD. Commit early and often. Tests green before every commit.
- When the phase backlog is empty: run the gate script; if it passes, seed the next
  phase's queue per §7 and stop; if it fails, convert each failing check into a queue task.
- Always end by updating HANDOFF.md (one-paragraph summary + blocked list) and pushing.
- Never: touch `C:\Users\openclaw0123\PostMule` or any credential file; create `v*` or
  `approved/*` tags; edit the `phase` field; delete anything (soft-delete invariant);
  start a second task; spawn subagents.

---

## 5. Self-healing — enumerated failure modes and responses

| # | Failure | Detection | Automated response |
|---|---|---|---|
| 5.1 | **Token exhaustion** (expected) | claude -p exits non-zero, limit message in log tail | Record `rate_limited`; exit clean. Next 5-hour-aligned run retries. Costs ~0 tokens. |
| 5.2 | **Crash / power loss / timeout kill mid-run** | Stale lock (dead PID) or dirty tree at postflight | `recover.ps1`: commit all WIP to branch `autopilot/recovery-<ts>`, push it, hard-reset main to origin, log recovery record. Charter step: each run checks for `autopilot/recovery-*` branches — harvest usable work or file an issue and delete reference. Nothing is ever lost; main is never left dirty. |
| 5.3 | **Broken main** (bad commit landed, or CI red) | Preflight probe red | Doctor mode: the entire run is devoted to fix-or-revert. `doctor_failures` counter in STATE.json. |
| 5.4 | **Doctor can't fix it** | `doctor_failures ≥ 2` | Wrapper sets `paused=true`, files P0 issue "Autopilot paused: main is red" via `gh`. Stops burning tokens until a human (or interactive session) intervenes. |
| 5.5 | **Stuck task** (agent fails same task twice) | `attempts ≥ 2` on a queue task | Task marked `stuck`, `gh issue` filed/commented with both run logs referenced, queue moves on. Never loops on one task. |
| 5.6 | **Silent death** (scheduler broken, auth expired, repo unreachable) | `watchdog.ps1` (separate daily task, pure PowerShell, zero tokens): last successful run >24h old, or paused, or stale lock, or `git ls-remote` fails | Files/updates a pinned "Autopilot status" GitHub issue — the notification channel the owner already watches. |
| 5.7 | **Push rejected / divergence** | git exit codes in step 4/7 | Recovery branch for local work, hard-sync to origin. Origin always wins; local work is preserved on a branch, never merged blind. |
| 5.8 | **Overlapping runs** | Lock with live PID + Task Scheduler "do not start new instance" (belt and braces) | Second run exits immediately, records `skipped`. |
| 5.9 | **Runaway run** | 90-minute hard timeout in wrapper | Kill process; 5.2 recovers on next run. |

---

## 6. STATE.json schema (committed; `phase` writable by gate scripts only)

```json
{
  "phase": 0,
  "paused": false,
  "mode": "normal",
  "doctor_failures": 0,
  "queue": [
    { "id": "p1-fix-103", "phase": 1, "issue": 103, "status": "pending", "attempts": 0,
      "desc": "Fix logs test that fails when a live install has a log file for today" }
  ],
  "last_run": { "ts": "2026-06-10T14:05:00Z", "outcome": "success", "task": "p1-fix-103" }
}
```

RUNS.jsonl record (local telemetry):
`{ "ts_start", "ts_end", "model", "mode", "task", "outcome", "commits": [], "log": "logs/run-<ts>.log" }`

---

## 7. Phase backlogs (seeded into the queue when each phase opens)

- **P0:** build everything in §2; register tasks; one supervised smoke run.
- **P1:** #103 fix → verify #101/#102 fully closed (wizard residue) → #104 Expert
  Directory → label sweep (`blocked:human` on #30/#87/#91/#93, `post-release` on #97 —
  makes gate-1's issue query well-defined) → file Ollama-provider enhancement issue
  (deferred per v1 analysis) → docs currency sweep.
- **P2:** build `validation/sandbox-install.wsb` + driver script (fresh Windows Sandbox →
  run setup.ps1 → `postmule --version` → fixture dry-run → emit `INSTALL_SMOKE_PASS` +
  setup.ps1 hash) → execute → attach evidence to #96 and close.
- **P3:** CHANGELOG.md → version bump → README release section → push `v0.1.0-rc.1` →
  confirm CI artifact build → #97 written options report (research, feeds the approval
  issue) → file "Release approval requested" issue with staged approval command.
- **P4:** run `release.ps1` (§8). Post-release: update README link, close release issue.
- **P5 (owner-triggered):** staged checklist for the live run when a VPM email arrives;
  evidence log → close #30/#93.
- **P6:** re-register schedule at daily cadence; triage-only charter addendum.

---

## 8. `release.ps1` — the only path to a version tag

1. Refuse unless: `STATE.phase == 3`, working tree clean, on main, synced with origin.
2. Refuse unless `approved/v0.1.0` exists on origin (annotated, owner-created).
3. **Re-run gates 1, 2, 3 fresh** (principle 2). Any failure aborts with a report.
4. Tag `v0.1.0` (annotated), push → triggers the release workflow.
5. Poll `gh run watch` for the release workflow; on failure → delete nothing, mark the
   GitHub release as draft if created, file P0 issue, exit 1.
6. **Post-release verification:** download the published release asset via `gh release
   download`, install it in a fresh Windows Sandbox (same driver as gate-2 but sourcing
   the *released artifact*, not the repo), smoke test. Failure → mark release as
   pre-release, file P0 issue. Success → tag `gate/p4-released`, advance STATE to 4.

A release therefore requires, in one unbroken chain: green local suite ×2, green CI ×2,
fresh-machine install proof ×2 (repo + released artifact), rc artifact build, and an
explicit human approval tag. Five independent machine gates + one human gate.

---

## 9. Token budget & cadence

- **Engine:** `--model sonnet --fallback-model haiku`. Fable 5/Opus reserved for owner
  sessions. All gates, recovery, watchdog, release = pure PowerShell, **zero tokens**.
- **Cadence:** every 5h (Pro window reset). Each run ≤1 chunk, ≤90 min. If runs visibly
  crowd out interactive use, drop to 2/day by re-running `register-tasks.ps1 -Cadence 12h`.
- **Context discipline:** charter caps file reads (read only what the task touches),
  forbids subagents, forbids re-reading CONTEXT.md unless the task needs it.

## 10. Build order (each chunk committed; harness builds itself under supervision first)

1. AUTOPILOT.md + run-autopilot.ps1 + recover.ps1 + STATE.json + gitignore entries; manual smoke run.
2. gates/ + watchdog.ps1 + register-tasks.ps1; gate-0 passes → `gate/p0-bootstrap`.
3. Supervised harness run executes #103 end-to-end (acceptance test of the whole loop).
4. Register schedule; observe two unattended runs from logs; tune charter; hands off.

## 11. Alternatives considered (unchanged from v1)

/loop (dies with terminal), cloud routines (no access to this machine — installer and
sandbox validation are inherently local), custom API daemon (API billing ≠ Pro
subscription), council debate (architecture cleared the 95% bar; mechanics above are
standard CI/state-machine practice — the risk was under-specification, fixed here, not
wrong direction).
