# story-drafting

The story-drafting skill: a two-step agent skill backed by a durable Restate
workflow. Step 1: an agent turns a job-to-be-done into drafts. Step 2: the
developer picks one — and the JTBD waits at the pick, durably, until they do.

## The job-to-be-done

> **When** I'm working through a multi-step piece of work with an agent
> (design something, get my sign-off, then build it),
> **I want** the steps and the checkpoints where I weigh in to be fixed in
> advance and to survive across sessions,
> **so I can** step away, come back, and resume at the step we were on, with
> what was decided so far, instead of re-explaining and hoping the agent
> follows the procedure this time.

## Language

- **Job-to-be-done (JTBD)** — what the developer is trying to get done. It is
  what they submit and what they come back to: a submitted JTBD holds its
  drafts, its picked draft, and the step it is at.
- **Submit** — hand a JTBD to the story-drafting skill so drafting begins.
- **Step** — one of the story-drafting skill's parts, fixed in advance and in
  order. A submitted JTBD is always at one step: *drafting*, then *the pick*. "Waiting for my pick"
  means it is at the pick.
- **Checkpoint** — a step where the developer weighs in. In this user story
  the pick is the checkpoint.
- **Draft** — a candidate user story the agent wrote for a JTBD.
- **Pick** — the developer choosing one draft; the chosen draft is the
  **picked draft**.
- **User story** — kept for the story this app is built from (below), never
  for a draft.

## The user story being built

**As a** developer, **I want** to submit a JTBD to the story-drafting skill and
have it stop for my pick once the drafts are written, **so that** the agent
cannot skip my checkpoint.

- **Given** a job-to-be-done,
- **when** I submit it to the story-drafting skill,
- **then** I can come back to it right away, before its drafts are written,
- **and when** I come back to it once they are written, it is at the pick, at
  least one draft is there to pick from, and no draft is picked yet.

## Constraints on the build

- Each submitted JTBD is worked through by a durable workflow on Restate;
  waiting for the pick is waiting on a durable promise.
- Drafting is done by a language model behind a port. No test calls a real
  model: the host the acceptance test drives is served with a deterministic
  drafting adapter, selected through the environment.
- The acceptance test is a root test (`docs/design-test-tiers.md`): it drives
  the app only through a running host the developer or an agent would use,
  speaking the app's protocol, and reads the result back through that host.
  The user story's behaviour scenarios are context tests.
- Out of scope for this user story: making the pick, revising a draft, and the
  story-drafting skill's agent-facing document (`SKILL.md`).
