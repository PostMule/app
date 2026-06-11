# PostMule — Claude Code Project Context

> Maintenance: before adding anything here, ask — is this derivable from the code or docs/ in under 3 file reads? If yes, don't add it.
> Reference (tech stack, module map, workflow, dev commands): CONTEXT.md — read on demand, not every session.

## Session Start — Required
1. Run `git log --oneline -15` and `git status` — commit and push any uncommitted/unpushed changes first
2. Check Architecture Invariants below — flag any drift before proceeding

## Session End — Required (before handoff)
1. Commit all changes
2. `git push` — branch must be current with origin before updating HANDOFF.md
3. Update HANDOFF.md
4. Confirm push succeeded (`git status` shows "nothing to commit, working tree clean" and "Your branch is up to date")

## Architecture Invariants (non-negotiable)
- Every external service accessed through a provider interface in `postmule/providers/*/`
- JSON files are source of truth — Google Sheets is a generated view, never written to directly
- Soft deletes only — max 0 auto-deletes ever
- All Drive writes: execute → MD5 verify → audit log
- Dry-run mode (`--dry-run`) respected by every agent and provider
- App LLM API safety limits (config: `api_safety`) checked before every LLM call
- Max 50 files moved per run
- No credentials or sensitive values ever in GitHub (`config.yaml`, `credentials.yaml` gitignored)

## Bill Matching (non-obvious)
- Exact amount + exact date required; company name NOT used (finance providers overwrite it)
- ACH descriptor and statement date planned (issue #27)
- Manual approval on by default; approval updates finance provider transaction name
