# Baseline learnings

What each iteration of the story-drafting baseline changed, what it showed,
and what it taught. The numbers come from `results/<trial>.json`; what each
trial decided (its generator spec and root tests) is in `results/<trial>/`;
the full tree each trial left is at `refs/trials/<trial>` on the remote
(`git fetch origin 'refs/trials/*:refs/trials/*'`).

Every trial's `conditions` block records what it actually ran under, read
from its own transcript: the effort each request recorded, how it was
spawned, and a hash of its system prompt. Trust those over the trial's name.

## Red, by iteration

| Iteration | What changed | Calls | Time | Findings |
|---|---|---|---|---|
| v1 (`red-1`, `red-2`) | first red prompt | 23–51 | 3–9 min | 6–20 |
| v2 | root tests reach the app only through a running host (TB070) | 46–61 | 9–11 min | 4–27 |
| v3 | the skill routes a new app through the generator | 20–28 | 2.5–3.3 min | 1 |
| v4 | context compiled into the prompt; generator writes into the scaffold; orphan scaffold; the arm serves the host | 9–12 | 110–160 s | 0 |
| v5 | `calling_mode`; no reads before generating; one `scripts/verify` run with its log; the commit command | 4–5 | 107–117 s | 0 |
| v6 | the user story cut to one Given/When/Then | 3–4 | 56–62 s | 0 |
| v7 | `--print` returns the generated root test | 3–4 | 50–58 s | 0 |
| v8 | models: Sonnet, Haiku, Opus (effort did **not** vary — see below) | 3–15 | 36–157 s | 0 |
| v9 | model × effort, 3×3, effort confirmed per transcript | 4–19 | 43–227 s | 0 |

All red trials from v3 on fail at the user story's *then* and nowhere earlier.

## What the iterations taught

- **The generator removes structure work; tessercheck findings disappear.**
  v2→v3 went from ~25 findings and ~10 minutes to 1 finding and ~3 minutes
  with the same code size. The one v3 finding (`start_run`, TB085) was a name
  the generator accepted and the analyzer refused; the generator now refuses
  it up front.
- **Red has two decisions; everything else should be mechanical.** The spec
  (domain model and names) and the acceptance test (how the *then* shows over
  the protocol). Calls fell from ~23 to 3–4 by removing the rest: compiling
  context into the prompt, generating into the scaffold, an arm that serves
  the host, one verify run with a kept log, a given commit command, and
  `--print` for the file the trial replaces.
- **Divergence traces to the requirements, not the model.** `stage` vs
  `status`, `job` vs `situation`/`motivation`/`outcome`, and "right away"
  each split trials because the story or its language left them open. The
  fix is in the story: one Given/When/Then per scenario, a Language section,
  no word with two meanings (a bare "job" is never a JTBD).
- **The generator's shape shows up in the contract.** Every aggregate field
  is a POST body field, so a field the system sets (`step`) either gets
  submitted by the caller or left out of the read. `start` mode's write
  answers before the workflow saves, so no test can read back "right away"
  without retrying (issue #7).
- **Model matters for the decisions; effort mostly changes time.** Sonnet
  and Opus made correct decisions at every effort; Haiku made the step a
  field the caller submits and chose `run` in all six trials, at 3–5× the
  calls. Opus took 54 / 60 / 99 s at low / medium / high with identical specs.
  Sonnet at low effort was fastest with correct decisions; at medium and high
  it modeled the JTBD as situation / motivation / outcome. n = 1 per arm.

## Red on the spec formats (red-specs)

| Iteration | What changed | Calls | Time | Findings | Gate |
|---|---|---|---|---|---|
| s1 (Sonnet, low, ×3) | red writes composition, implementations, and sample values from the language and story specs, renders with `srv.cli.render` (render-8), and writes one acceptance test per level-2 story | 7–9 | 135–139 s | 0 | through the non-root tiers; s-1-a-1 passes (the stubs satisfy it), s-2-a-1 fails at its then |
| s2 (Sonnet, low, ×3) | the renderer refuses a class of actions not named for a language code name, and the format reference states the rule | 7–9 | 131–144 s | 0 | same as s1 |

- **Red reproduced the reference composition** (`generator/compositions/story-drafting/`, written by hand) in every trial: the same aggregate contract (spec, `record_stories` and its three outcomes, reads), the same client steps (issue, save before start, `start_`), the same orchestrator steps and signal, ports, shapes, enums, and messages. The one difference, identical in all three: the class of actions on `StoryDrafter` is named `drafter`, not `story`. The language has no term that names it, so the language left it open.
- **s2 closed the naming gap:** with the rule stated and enforced, all three named the class of actions `story`, and every compared key of all three compositions matches the reference. All three committed.
- **One trial (s1-1) did the work but never committed** and handed back "placeholder"; its specs and test are copied into `results/red-s1-sonnet-low-1/` from its worktree. A process failure at low effort, not a design one.
- Calls include one Read of the prompt file (40 KB, handed over as a file).

## Green, by iteration

| Iteration | What changed | Calls | Time | Files changed | Findings |
|---|---|---|---|---|---|
| v2 | host-only root tier | 45–53 | 9–13 min | 40–45 | 5–18 |
| v3 | from generator-built red trials | 50–56 | 12–26 min | 40–46 | 0–5 |
| v4 | from a tree rendered from the five-spec formats (scaffold g5): the contract generated, green owning only the aggregate module and the template drafter; compiled prompt | 9–14 | 3.3–3.7 min | 4 | 0–1 |

- **The generated contract removes green's structure work.** Every v4 trial changed exactly its four owned files (the domain module, the drafter, their tests), passed the drift check, left the acceptance tests unchanged, and reported no contract gap. v3 trials built ports, actions, relays, and the signal by hand and reworked start-and-return.
- **What is left is story behavior, and it converged.** All three derived status from the stories, answered `record_stories`' three outcomes the same way, added the same two value objects (`StoryText`, `StoryTexts`) to keep TB083, and refused blank text. They differed only in the drafter's template wording and story count (one or two).
- **Calls include one Read of the prompt file:** the compiled prompt (80 KB) was handed over as a file rather than inline.

## Harness pitfalls

- **A named Agent spawn ignores the agent definition.** Spawning with a
  `name` makes an in-process teammate that gets the teammate system prompt
  and the session's effort; the `subagent_type` definition's `effort` and
  body never apply. v8's low/default/high arms all ran at medium. Spawn
  trials unnamed to apply a definition, and check `conditions.effort`.
- **Unnamed spawns get a different system prompt** (the definition body plus
  a short agent block, 1,475 chars) than named teammates (Claude Code's full
  prompt plus a team block, 8,750 chars). Compare trials only within one
  `conditions.system_prompt` hash.
- **Haiku 4.5 records no effort**, so effort arms for it are one condition.
- **A trial's scratchpad is not a record.** v1–v3 specs lived in agent
  scratchpads; `prepare` now names the spec path so `record` keeps it.
