# A/B: the tesser pipeline against a bare agent (story-drafting)

Same product, two ways. **Arm A** is red then green from three specs
(`story-drafting/specs/language.toml`, `story.toml`, `infra.toml`: what the
product means, what a user must be able to do, and what it runs on) on the
current story-drafting scaffold. **Arm B** is one bare agent in an empty
repository outside this tree, given `prompts/bare.md`: the same facts as the
three specs in prose (fidelity-reviewed against them, twice), and nothing else
except the disclosed harness facts (the port it must listen on, `.venv`, the
checker, and what a restart means).

Every agent in both arms is the same definition (`~/.claude/agents/tesser-red-trial-medium.md`:
effort medium, one generic body; the model is passed per call), spawned unnamed
so the definition's effort applies, so all runs share one system prompt. The same check (`check.py`) runs on each
arm's output: it serves the output, registers the Restate endpoint, and drives
the two level-2 stories over HTTP, tolerant of what the specs leave open (id
shape, extra keys, how long drafting takes).

## Running a round

`round` runs a whole round the same way every time: every cell, N samples,
in waves across the Restate slots, with every metric recorded.

    scripts/baseline/ab/round plan ab4 --models opus,sonnet --n 3 --scaffold story-drafting-scaffold-s8
    scripts/baseline/ab/round next ab4          # prints the launches as JSON
    #   start every printed launch in one message: Agent, unnamed, with its
    #   subagent_type, model and prompt verbatim (named spawns ignore the
    #   definition's effort). Then, as each agent finishes:
    scripts/baseline/ab/round done ab4 <run> <agent-id>
    scripts/baseline/ab/round next ab4          # a finished red frees its green; a finished sample frees its slot
    #   ...until status shows every run done or blocked...
    scripts/baseline/ab/round review ab4        # cold codex review of every finished tree (up to ~25 min; run it in the background)
    scripts/baseline/ab/round report ab4        # results/ab4-metrics.json and ab4-table.md
    scripts/baseline/ab/round push-refs ab4     # arm A trees to refs/trials/<run>

Then write `results/<round>.md`, reading the generated table, and commit the
records `done` wrote (`scripts/baseline/results/<run>*` for arm A,
`results/<run>.json` and `<run>-check.json` here) with it.

What `round` does for you:

- **Scheduling.** Each sample holds one slot (1-9 by default), so up to nine
  samples run at once. Arm A's green uses its red's slot. A slot whose host
  ports something already listens on is skipped. Run one round at a time
  across sessions: slots are machine-wide.
- **Setup kept equal.** `plan` warms pip's cache with the packages a bare
  agent usually installs, so no bare run pays for a download another did not.
- **Measuring.** `done` kills whatever the run left listening on its ports
  (only processes running from the run's own tree), then measures the run:
  `measure` for red and green, plus the shared check for green, and
  `measure-bare` for bare. `measure-bare` also runs the agent's own pytest
  suite, if it wrote one.
- **Failures.** A run whose prepare fails is marked blocked with the reason,
  and the rest of the wave goes on. `prepare` removes whatever it made
  before failing.
- **Reviews.** `review` runs `codex-review` on every finished sample's final
  tree at once (arm A's green tree, arm B's project), under labels shuffled
  with a recorded seed. It writes `results/<run>-codex.txt`. The report lists
  each review's findings and changeability verdict under its cell, unscored:
  a review is part of the round's record, not yet one of its metrics. A
  sample is reviewed once, so running `review` again reviews only what was
  not reviewed.
- **The report.** It reports each cell's median and range over its samples:
  agent time and its split, calls, API requests, tokens, the shared check
  (per story, plus the probes), tests, coverage, tessercheck findings, green's
  integrity, and files and lines. It also records, for each sample, the most
  other agents that ran at the same time, because timings from rounds of
  different concurrency are not comparable.

## Running one run by hand

    scripts/baseline/ab/prepare-bare <run> <slot>          # arm B
    scripts/baseline/ab/measure-bare <run> <transcript>    # arm B: metrics + check
    scripts/baseline/ab/check-tree A|B <run>               # the shared check, alone

Arm A uses the existing `prepare red-specs ...`, `prepare green-on-red <red
branch> ...`, `measure`, then `check-tree A <green run>`.

Reported per arm: agent time and calls per phase, the shared check's result,
files and lines. Agent time is split by what the agent was waiting on
(`metrics.time_split`): checking its work (the gate, tests, the analyzer),
setup (a virtualenv, installs, containers), probing the served service by hand
(curl, running `main.py`), other tool calls, and the model's own time, which is
the time in no tool call. Arm A's end-state gate, run by `measure` after the
agent finishes, is not agent time.

Neither prompt asks for more than the stories require. Until run 2 the bare
prompt said to build "the wait at the checkpoint" on Restate, which no story
asks for and red never built; from run 3 it says only "Build the workflow
(story drafting) on it".
