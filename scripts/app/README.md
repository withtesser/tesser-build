# Building a rendered app: specs, red, green

A rendered app is a top-level directory whose tree `srv.cli.render` writes
from its specs, and which a red and then a green agent complete. The
`story-drafting` app is one; the trial harness (`scripts/baseline/`) measures
the same pipeline. This is the direct path: one app, in this checkout, with you
orchestrating.

| Tool | Does |
|---|---|
| `scripts/app/new-app <app>` | adds `<app>/specs/`, `.tesser-root`, the manifest row, the verify arm (`run_rendered_app`), and a CI job |
| `scripts/app/prompt red\|green <app>` | fills the red or green prompt for this checkout and prints the message to start the agent with |
| `scripts/verify <app>` | the app's gate: the render check, tessercheck, `mypy --strict`, then one plain `pytest` (the tests start their own engines and serve the host) |

The prompts are the trial harness's (`scripts/baseline/prompts/red-specs.md`
and `green-on-red.md`), filled by `scripts/baseline/render_prompt.py` with the
app as `{tree}`. The filled prompts and the agents' gate logs go to
`.baseline-runs/app-<app>/`.

## The steps

1. **Branch.** Work in a worktree branch, as for any change
   (`.claude/worktrees/<name>`).
2. **Create the app:** `scripts/app/new-app <app>`.
3. **Write the specs** with the `tesser-app-specs` skill: `language.toml`,
   `story.toml`, `infra.toml` in `<app>/specs/`. Approve them, and commit them.
4. **Red.** Run `scripts/app/prompt red <app>` and start an agent with the
   message it prints. Start it unnamed, with an agent type whose effort you
   want (for example `tesser-red-trial-medium`) and a model. Red writes
   `composition.toml`, `implementations.toml` and `generator.toml`, renders the
   tree, fills in the acceptance tests, and commits.

   Check before going on:
   - The gate log (`.baseline-runs/app-<app>/red-verify.log`) fails only in
     pytest, only on acceptance tests in `<app>/tests/`, and each fails at its
     story's *then*.
   - The acceptance tests say what the stories say, no more and no less. This
     is the cheapest place to catch a misunderstanding.
5. **Green.** Run `scripts/app/prompt green <app>` and start an agent with its
   message. Green writes the aggregate, the agent-owned stores and gateways,
   and their tests, and commits once `scripts/verify <app>` is green.

   If green reports a **GAP** (the contract lacks something a story needs), it
   stops without working around it. The fix is in the composition: correct
   `composition.toml` (by hand, or with an agent given the gap) and render
   again, which keeps every file an agent owns; then run green again. If the
   gap is really in the stories, go back to step 3.
6. **Ship.** Run `scripts/verify <app>`, and open a PR.

A level-2 story with no route (a restart, a background effect) gets no
acceptance test. Check it by hand: serve the app, drive the story, and
restart the host if the story says so.
