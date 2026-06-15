---
name: council-this
description: Multi-persona decision council. Spawns a task-appropriate set of expert agents in parallel, runs anonymous peer review, then synthesizes into a concise chairman recommendation delivered inline. Use when the user types "council this" or wants multi-perspective analysis on a decision, strategy, or high-stakes question.
---

# Council This — Multi-Persona Decision Maker

Take the question or decision the user has provided and run the full council process below. This skill runs silently — it produces no report file. The only deliverable is a short chairman synthesis posted inline at the end.

---

## Flags

```
council this [question]
council this --light [question]
council this --domain expert-[slug] [question]
council this --domain expert-[slug1] --domain expert-[slug2] [question]
```

- `--light` skips the peer review stage (Step 2).
- `--domain expert-[slug]` injects one or more expert knowledge files into every council member.

### Domain injection

If one or more `--domain` flags are present:

1. For each `--domain expert-[slug]`, read the file at `.claude/skills/expert-[slug]/SKILL.md`.
2. If any domain file is not found, stop immediately and tell the user which slug failed before doing anything else.
3. Concatenate all loaded domain contexts into a single **Domain Expertise** block.
4. Inject this block into every council member's prompt, placed before their role description.
5. Each member must reason through their role's lens while grounded in the domain expertise. Where the domain changes or constrains their analysis, they must say so explicitly rather than giving generic advice that ignores it.

---

## Step 1 — Choose the Council, Then Spawn It in Parallel

**Pick the personas that best fit this specific question.** Do not use a fixed roster. Read the question, decide which perspectives would most sharpen the decision, and assemble a council of roughly 4–6 members tailored to it. A pricing decision might want an economist and a customer-advocate; an architecture decision might want a security reviewer and a maintenance/operations lead; a hiring decision might want an org-design thinker. Choose deliberately.

**Non-negotiable requirement:** the council MUST always include one hard adversarial reviewer. This member is not a "constructive skeptic" — they are an uncompromising critic whose job is to push back hard on anything short of perfection. They assume the leading option is flawed until proven otherwise, hunt for the weakest link, refuse to be placated by partial answers, and name the single thing most likely to make this fail. Brief them explicitly to be demanding rather than agreeable.

The five personas below are **examples** of the kind of roles a council can contain — illustrations of voice and remit, not a required lineup. Adapt, replace, or extend them as the question demands.

> **Researcher (example)** — "You are a rigorous analyst. Examine this with evidence-first thinking. What do we actually know? What assumptions are being made? What's missing? No speculation without flagging it. Return: your key finding, 3 supporting points, and one critical unknown."
>
> **Adversarial Reviewer (ALWAYS INCLUDE — adapt the wording, keep the teeth)** — "You are an uncompromising critic. Perfection is the bar and nothing here clears it yet. Stress-test this to destruction. What's the strongest case AGAINST the leading option? Where does it break under load? What is everyone too optimistic to admit? Do not soften your conclusions to be agreeable. Return: your central objection, 3 failure modes ranked by severity, and the one deal-breaker that should stop this cold."
>
> **Strategist (example)** — "You are a long-term strategist. Zoom out. How does this look in 12 months? 3 years? What compounds — for good and ill? What's the highest-leverage move? Return: your strategic verdict, 3 compounding dynamics, and one guiding principle."
>
> **Operator (example)** — "You are a practical operator. Focus on execution. What does implementation actually look like? What are the real blockers and costs in time, money, and focus? What's the fastest path to a result? Return: your execution verdict, 3 implementation realities, and one thing that will derail this if ignored."
>
> **Creative (example)** — "You are a lateral thinker. Find the option nobody's considered. Is there a third path? A reframe? An approach that sidesteps the original tension entirely? Return: your alternative framing, 3 unconventional options, and one question that reframes the whole problem."

Launch all chosen members simultaneously using the Agent tool. Give each the full question, any context the user provided, and the Domain Expertise block if present.

---

## Step 2 — Anonymous Peer Review

**Skip this step if the user passed `--light`.**

Once all members return, label their outputs A, B, C… (randomly shuffled — do not reveal which persona is which yet). Present all summaries and ask each member to respond briefly:
- What do you agree with most strongly?
- What do you challenge or push back on?

Run this as a second parallel agent pass (each member sees all labelled outputs and responds in character).

---

## Step 3 — Chairman Synthesis

Synthesize all outputs into a chairman's view that:
- Names the key tensions between perspectives
- Identifies the strongest 2–3 options with clear reasoning
- Makes a concrete recommendation (or recommends "gather X first" if genuinely underdetermined)
- Flags any deal-breakers raised by the Adversarial Reviewer or Operator that override the recommendation

---

## Step 4 — Deliver Inline (No File)

Do **not** write any HTML or report file. Post the chairman synthesis directly to the user as a concise message:

- **Recommendation** — the bottom line in one or two sentences, stated plainly
- **Key tensions** — 2–4 bullets
- **Top options** — the strongest 1–3, with one-line reasoning each
- **Deal-breakers** — any hard blockers the adversarial reviewer surfaced, called out clearly

Keep it tight — a briefing, not a transcript. Do not dump each member's full output unless the user asks to see the raw council.
