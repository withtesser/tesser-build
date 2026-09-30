You are working alone in {workdir}, an empty git repository. Every file you
read or write and every command you execute is in that directory: use absolute
paths, and `cd {workdir}` at the start of each shell command. No human will
answer questions: make each decision yourself and keep going. Do not spawn
subagents. When you are done, commit your work and reply with a short summary
of what you built and how to run it.

Build the story-drafting HTTP API.

## What it is for

A developer works through a multi-step piece of work with an agent (design something, get their sign-off, then build it). They want the steps, and the checkpoints where they weigh in, to be fixed in advance and to survive across sessions, so that they can step away, come back, and pick up at the step they were on, with what was decided so far, instead of re-explaining and hoping the agent follows the procedure this time.

## Words this system uses

Use these words, and not the ones after "not". Where a word below gives a name in backticks, the HTTP API uses that name exactly, as a route, JSON field, or value.

- **story-drafting skill**: a procedure an agent follows with the developer, in fixed steps with checkpoints: story drafting for a job to be done, then wait for the developer's acceptance. (Not: harness, workflow, flow.)
- **job to be done** (JTBD): what a developer needs done, written as "as / I want / so that", naming no solution. What the skill runs on: it holds its stories and has one checkpoint. (Not: job, task, goal, story draft, draft, run.) Its fields are `role` (the "as" part), `i_want`, and `so_that`; its identity is `jtbd_id`.
- **story**: one given / when / then that would fulfil its job to be done, with a story state. (Not: user story, scenario, requirement, story draft.) A job to be done's stories are `stories`; each has `given`, `when`, `then`, and `state`. Stories take the same given / when / then shape as the stories in "What a developer must be able to do" below.
- **story text**: the given / when / then a story drafting produces, before the job to be done gives it a state. (Not: drafted story, draft.)
- **recording stories**: keeping a story drafting's story texts as the job to be done's stories, each drafted. (Not: saving stories, storing stories.)
- **story state** (`state`): where a story stands: `drafted` (written, not yet decided), `accepted` (the developer keeps it), rejected (the developer does not). (Not: picked, approved, declined, pending.)
- **story drafting**: the step in which story texts are written for a job to be done. A story drafting yields at least one story. (Not: drafting, composing, writing, generating.)
- **status** (`status`): where a job to be done stands, following from its stories' states: `drafting_stories` (none yet), `awaiting_story_acceptance` (any story drafted).
- **checkpoint**: a point in the procedure where the developer weighs in, fixed in advance, that the agent cannot skip. A job to be done has one: after story drafting, it waits for the developer's acceptance. (Not: gate, approval step.)
- **accept**: what the developer does at the checkpoint: one decision over the drafted stories — the stories named are accepted, the rest rejected. (Not: pick, approve, choose, select.)
- **reject** (not yet settled): the other half of the same decision: a drafted story the developer does not name when accepting. (Not: decline, discard, drop.)
- **submit**: hand a job to be done to the story-drafting skill, which begins its story drafting. (Not: start, begin, open, create.)
- **revise**: having a job to be done's stories drafted again with the developer's note. Out of scope; it would add story drafting rounds and reopen the one-round decision below.

Decisions already made:

- What holds one start of the skill? The job to be done itself. No separate story draft, draft set, or run.
- How many stories does one acceptance take? Any number: one decision over the set — the stories named are accepted, the rest rejected. One acceptance per job to be done, made once.
- Can a job to be done be drafted more than once? Not for now: one story drafting round, one checkpoint, and the job to be done's id is the key for that round. Revise would reopen this.

## What a developer must be able to do

1. **Given** a job to be done, **when** I submit it to the story-drafting skill, **then** I can come back to it, and I can see it is drafting its stories.
   - Over HTTP: **given** a job to be done's `role`, `i_want`, and `so_that`, **when** I POST them as JSON to `/jtbds`, **then** I get back 201 with its `jtbd_id` and `status` `"drafting_stories"`.
2. **Given** a job to be done whose stories have been drafted, **when** I read the job to be done, **then** its stories are given to me, each one drafted and none accepted, and it is awaiting my acceptance of its stories.
   - Over HTTP: **given** I have created a job to be done with `POST /jtbds`, and its stories have been drafted, **when** I `GET /jtbds/{jtbd_id}`, **then** I get back 200 with `status` `"awaiting_story_acceptance"` and at least one story, each with a `given`, a `when`, and a `then`, and in `state` `"drafted"`.
3. **Given** a job to be done I submitted, whose stories have been drafted, and the service has since been restarted, **when** I read the job to be done, **then** it is still there, with the same stories, each still drafted, and it is still awaiting my acceptance.
   - Over HTTP: **given** I have created a job to be done with `POST /jtbds`, its stories have been drafted, and the service has been restarted, **when** I `GET /jtbds/{jtbd_id}`, **then** I get back 200 with `status` `"awaiting_story_acceptance"` and the same stories, each with a `given`, a `when`, and a `then`, and in `state` `"drafted"`.

## Out of scope

Accepting stories (and so rejecting the rest); revising a job to be done's stories; story drafting with a language model; the agent-facing skill document (SKILL.md).

## Running it

"The service has been restarted" means: its process is stopped and started again with the same command and environment, while the Restate server keeps running.

The service is a Python 3.12 program. To be checked, it must listen on the port in the environment variable `PORT` (host 0.0.0.0) and be started from the project root with `.venv/bin/python main.py`. Create the virtualenv `.venv` in the project root and install what you use into it; third-party Python packages are allowed.

The service runs its workflow on Restate, a durable-execution server, and one is already running for you: its ingress, through which the service starts its workflows, is at `$RESTATE_INGRESS`, and its admin API at `$RESTATE_ADMIN`. Build the workflow (story drafting, and the wait at the checkpoint) on it, using the `restate-sdk` Python package. Serve your Restate endpoint at `/restate` in the same process, on the same port; before checking, the checker registers `http://host.docker.internal:$PORT/restate` with the admin API. Jobs to be done are kept in a SQLite database file, at the path in the environment variable `JTBD_DB_PATH`; a service that is stopped and started again reads the same file.

The checker sets `PORT`, `RESTATE_INGRESS`, `RESTATE_ADMIN` and `JTBD_DB_PATH` itself. For your own testing, use `PORT={port}`, `RESTATE_INGRESS={ingress}`, `RESTATE_ADMIN={admin}` and `JTBD_DB_PATH={dbpath}`.
