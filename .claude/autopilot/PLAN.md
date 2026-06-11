# PostMule Autopilot — Deployment Harness Plan

> Status: DRAFT — awaiting owner approval (session 2026-06-10).
> Goal: drive PostMule to "fully deployed" with near-zero owner effort, on a Pro-plan
> token budget, with automatic recovery when usage limits interrupt a run.

## Definition of Done ("fully deployed")

1. All automatable open issues closed (#103, #104, residual wizard polish).
2. v0.1.0 release tagged and published; README links to Releases page.
3. Installer validated on a clean machine (#96) — automated via Windows Sandbox where possible.
4. Live end-to-end pipeline validated (#30, #93) — requires real mail arriving; owner-triggered.
5. Docs current (CLAUDE.md/CONTEXT.md/README/mockup match reality).
6. Owner's remaining effort reduced to one short checklist (DNS, release approval, live-run trigger).

## Architecture (chosen path — confidence ≥95%)

**Windows Task Scheduler → `run-autopilot.ps1` → headless `claude -p` (Sonnet) → one bounded
work chunk → commit + push + HANDOFF.md update → exit.**

- **Scheduler, not /loop or cloud routines.** /loop needs a terminal left open and dies on
  reboot. Cloud scheduled agents can't touch this machine (installer tests, Task Scheduler,
  Windows Sandbox, live install at `C:\Users\openclaw0123\PostMule`). Task Scheduler survives
  reboots and is already the pattern PostMule itself uses.
- **Cadence: every 5 hours** (Pro usage windows reset on a 5-hour rolling basis). If a run
  starts with no tokens available, `claude -p` fails fast and cheap; the next run picks up.
  This *is* the self-healing token behavior: no polling, just scheduled retries aligned to
  the reset cadence.
- **Model: `--model sonnet` with `--fallback-model haiku`** for autopilot runs. Opus-class
  models burn Pro limits several times faster; Sonnet is fully capable of executing a
  well-specified charter. Fable 5/Opus reserved for interactive design sessions with the owner.
- **State = git + HANDOFF.md** (already battle-tested in this repo for months). Every run:
  commit early, commit often. A run killed mid-chunk leaves uncommitted work that the next
  run's session-start protocol (commit-first rule) recovers or reverts. No new state format
  to maintain; `automation` state lives where humans already look.
- **One chunk per run.** The charter (AUTOPILOT.md) forbids starting a second work item.
  Bounded scope keeps token use predictable and failure blast radius small.
- **Overlap guard:** lock file + Task Scheduler "do not start a new instance".
- **Logging:** full `claude -p` output to `.claude/autopilot/logs/run-<timestamp>.log`
  (gitignored). HANDOFF.md carries the human-readable summary; git log is the journal.

### Permission mode (owner can veto)
Recommended: `--permission-mode acceptEdits` + expanded allowlist in `.claude/settings.json`
(pytest, git, gh, python module runs). If the agent hits a disallowed command it notes it in
the run log and HANDOFF "Blocked" section instead of stalling silently. `bypassPermissions`
is the zero-friction alternative but gives an unattended agent unrestricted shell on this
machine — not recommended as the default.

### Hard guardrails (in AUTOPILOT.md charter)
- Never touch `C:\Users\openclaw0123\PostMule` (live install) or any credential file.
- Never push a `v*` tag, close a release, or change anything outward-facing without an
  explicit "approved" marker from the owner in HANDOFF.md.
- Architecture Invariants in CLAUDE.md apply unchanged.
- Tests must pass before every commit; if unfixable in-session: file issue, revert, stop.
- Max one work chunk per run; update HANDOFF.md before exit, always.

## Backlog (priority order for the autopilot)

| # | Item | Automatable? |
|---|---|---|
| 1 | #103 — fix logs test on machines with live install | Fully |
| 2 | Verify #101/#102 closure; finish any wizard polish | Fully |
| 3 | #104 — bootstrap Expert Directory | Fully |
| 4 | #96 prep — Windows Sandbox (.wsb) script that runs setup.ps1 on a clean sandbox; owner just double-clicks and watches | Mostly |
| 5 | #87 attempt — auto-vectorize logo with vtracer/potrace; present result for owner judgment | Attempt |
| 6 | #97 — cloud deployment investigation → written options report for owner decision | Research only |
| 7 | Docs currency sweep | Fully |
| 8 | Release prep (CHANGELOG, README release link, tag command staged) | Prep only — tag push gated on owner approval |

**Blocked on owner (the entire human checklist):**
- Approve v0.1.0 release (one reply).
- #91 — DNS records at registrar (~10 min, instructions will be staged).
- #30/#93 — trigger one live run when a real VPM scan email arrives (semi-attended).
- Judge vectorized logo / sandbox install recording.

## Ollama / local llama — DEFERRED (file enhancement issue, do not install now)

Two different needs were conflated; neither justifies installing Ollama today:
1. **PostMule's app LLM** — default is Gemini 1.5 Flash *free tier*: already integrated,
   tested, and costs $0. An Ollama provider is a clean future enhancement behind the existing
   `providers/llm` interface (offline/privacy option) but advances deployment zero.
2. **Dev automation** — Claude Code cannot run on llama; local models can't replace the
   autopilot's engine. No token savings available there.

Action: autopilot files a `providers/llm/ollama` enhancement issue; revisit post-v0.1.0.

## Build plan (3 chunks, ~1 session)

1. **Chunk 1:** `AUTOPILOT.md` charter + `run-autopilot.ps1` + `register-autopilot.ps1`
   (schtasks, every 5h, no-overlap) + log dir + gitignore. Smoke-test with a trivial prompt.
2. **Chunk 2:** Expand permissions allowlist; run #103 end-to-end through the harness
   manually (`.\run-autopilot.ps1`) as the acceptance test.
3. **Chunk 3:** Register the scheduled task; observe two unattended runs; tune charter.

## Alternatives considered and rejected
- **/loop (interactive recurring):** dies with the terminal/reboot; owner must babysit.
- **Cloud scheduled agents (routines):** no access to this machine; deployment validation is
  inherently local. Could later supplement for pure-GitHub chores.
- **Custom Python daemon calling the Claude API:** API billing is separate from the Pro
  subscription — directly contradicts the token-budget goal.
- **Council debate:** skipped intentionally — the architecture choice cleared the 95%
  confidence bar (CLI flags verified locally; state mechanism already proven in this repo),
  and a 5-agent council would burn the very tokens this plan exists to conserve.
