# story-drafting

A two-step agent skill backed by a durable workflow. Step 1: an agent drafts
user stories from a job to be done. Step 2: the developer picks — and the run
waits, durably, until they do.

It is also this repo's baseline for measuring how agents build a tesser app
from one user story: first the red acceptance test, then the implementation
that turns it green. The tree here is the chosen green run (green-v2-1); the
baseline runs start from the empty scaffold tagged `story-drafting-scaffold-v2`
(`scripts/baseline/prepare red story-drafting-scaffold-v2 <run> <slot>`), and
their numbers are in `scripts/baseline/results/`.

## The job

> **When** I'm working through a multi-step piece of work with an agent
> (design something, get my sign-off, then build it),
> **I want** the steps and the checkpoints where I weigh in to be fixed in
> advance and to survive across sessions,
> **so I can** step away, come back, and pick up at the step we were on, with
> what was decided so far, instead of re-explaining and hoping the agent
> follows the procedure this time.

## The story being built

**As a** developer, **I want** to start the story-drafting skill on a job and
have it stop for my pick once the stories are drafted, **so that** the agent
cannot skip my checkpoint.

- **Given** a job to be done,
- **when** I start the story-drafting skill on it and the stories are drafted,
- **then** the run is waiting for me to pick, the drafted stories are there to
  pick from, and no story is accepted yet.

## Constraints on the build

- The run is a durable workflow on Restate; waiting for the pick is waiting on
  a durable promise.
- Drafting is done by a language model behind a port. No test calls a real
  model: the acceptance run selects a deterministic drafting adapter through
  the environment.
- The acceptance test is a root test (`docs/design-test-tiers.md`): it drives
  the app only through a running host the developer or an agent would use,
  speaking the app's protocol, and reads the result back through that host.
  The story's behaviour scenarios are context tests.
- Out of scope for this story: making the pick, revising a draft, and the
  agent-facing skill document (`SKILL.md`).
