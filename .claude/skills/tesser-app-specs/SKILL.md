---
name: tesser-app-specs
description: Write or revise the three human-owned specs of a rendered tesser app in this repo — language.toml (what our words mean), story.toml (what a user must be able to observe) and infra.toml (what it runs on) — from what the user describes, asking only to fill gaps or confirm. Use when the user wants to start a new app for the red/green pipeline, or change an app's language, stories or infra before red runs.
---

# Writing an app's specs

You write the three specs a rendered app starts from. They are the user's
(product owner's and engineer's) decisions, written down: the red agent designs
the composition from them, and nothing downstream may add to them. Write what
the user tells you; ask only where something is missing, ambiguous, or yours
would be a guess. Then hand them back for the user to approve.

The formats are documented once, in `generator/compositions/README.md`
(sections 1–3); `story-drafting/specs/` is a worked example of all three. Read
both before writing. The rules below are the ones that are easy to get wrong.

## Where

A new app is a top-level directory. If it does not exist yet, create it with

    scripts/app/new-app <app>

which adds `<app>/specs/`, its `.tesser-root`, the manifest row, the verify
arm and the CI job (the layout check fails without any of them). Write the
specs into `<app>/specs/`. The whole flow after the specs is in
`scripts/app/README.md`.

## `language.toml` — what our words mean

- `context = "<snake_case>"`, then one `[[terms]]` per term: `term`, `means`,
  and optionally `short`, `not` (words not to use for it), `status`, `note`.
- **Meanings only.** No rules ("a story is accepted once"), no design ("a
  durable promise"), no tooling, no code names. A rule belongs in a story, a
  design choice in the composition or infra, a scope decision in `story.toml`'s
  `[scope]`. If the user gives you one, put it where it belongs, not here.
- One term, one meaning; one concept, one term. Add a `not` list for the words
  people will reach for instead.
- Every noun a class of actions will act on needs a term (the red agent names
  classes of actions only for terms). If the stories revolve around a thing
  that has no term, ask.
- `status = "proposed"` for every term you write; the user makes it
  `"settled"`.

## `story.toml` — what a user must be able to observe

- A tree: level-1 JTBDs (`as` / `i_want` / `so_that`, in the user's words),
  each with stories; each story with level-2 JTBDs (the interface); each with
  level-2 stories.
- **A JTBD names no solution** at its level. "As a developer I want an HTTP
  API that..." is not a level-1 JTBD; "as a developer I want the checkpoints
  fixed in advance so that..." is. The level-2 JTBD's `as` is the interface
  (`the <app> HTTP API`), because level 2 is where the interface is chosen.
- **One given, one when, one then per story.** A second action is a second
  story, never an "and then when".
- **Level 2 names routes, fields and values exactly**, as the interface
  carries them. Each routed level-2 story has `route = "<METHOD> <path>"`
  (lowercase segments, `{field}` parameters) and `status = <2xx>`; its `when`
  says the method and path word for word, and its `then` says the status. Its
  `given` says in words how the state is reached ("I have submitted a loan with
  POST /loans").
- A level-2 story asserts only what its level-1 story observes. Edge cases,
  error responses and shapes belong lower down, not here.
- Write only what a story requires. Every enum value, request field, read,
  and non-success outcome the app will have must be named by some story; if
  the user wants a behavior, it needs a story; if no story needs it, it is out.
- `[scope] out = [...]` lists what is deliberately left out, in plain words.
  Ask about the obvious neighbours (the next step of the flow, failures,
  revisions) and record the answers.

## `infra.toml` — what it runs on

These are the engineer's technology decisions. **Ask; never infer them**, and
never fill one in from the example: `app`, `[runtime]`, the engine, the host,
each storage and its location variable, the listen port variable, and
`[variables]` saying what each one is. The format and the required keys are in
the README's section 3.

## What the renderer can build today

Check the user's app against this before the specs are approved, and say so
plainly when something is outside it. Red cannot render what the renderer does
not support, and no prompt fixes that.

- One bounded context and one aggregate per app, with commands and reads.
- Exactly one workflow (orchestrator operation), keyed by the aggregate's
  identity, whose steps run actions and may **wait** on a durable promise. A
  promise is never **resolved**: an approval, accept or reply step that
  completes the wait cannot be built yet.
- Restate as the engine and an HTTP host (GET, POST, PUT, PATCH, DELETE).
- Storage: `memory`, or a named storage with a location variable (for example
  SQLite), whose store class the green agent writes.
- Gateways (a port to anything outside) are written by the green agent. The
  pipeline provides no credentials and the gate runs offline, so a gateway to
  a language model or a paid service needs a decision in the specs: a fixed
  or templated body now (story-drafting's `[scope]` puts "story drafting with
  a language model" out), or credentials and a real service, which the user
  sets up.
- One acceptance test per routed level-2 story, one routed story per route. A
  level-2 story with no route (a restart, a background effect) gets no
  acceptance test.

## When to ask

Ask when:

- an infra decision is missing, however obvious it seems;
- a word could mean two things, or two words seem to mean one thing;
- a JTBD names a solution, or a story needs two whens;
- a level-2 story is missing its route, fields or status;
- the app needs something from the list above that the renderer cannot build;
- the edge of scope is unclear.

Otherwise, write. Batch your questions: one short list, each question with the
answer you would pick if the user has no preference.

## When you are done

Report the three files, the terms you left `proposed`, what you put in
`[scope] out`, anything outside the renderer's limits, and any question still
open. The user approves the specs before red runs; commit them on the app's
branch once they do.
