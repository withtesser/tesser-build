# Agent baselines

`story-drafting/` is this repo's baseline for measuring how agents build a
tesser app from one user story: first a red trial writes the failing
acceptance test, then a green trial makes it pass. The tree on the branch is
the chosen green trial (green-v2-1); trials start from a scaffold instead.

| Script | Does |
|---|---|
| `scaffold <tag>` | cuts a red scaffold: an orphan commit whose `story-drafting/` holds only its README, with `scaffold-arm.bash` as its gate arm |
| `prepare red\|green <base-ref> <trial> <slot>` | a worktree and a fresh Restate server for one trial, and its prompt rendered from `prompts/<phase>.md` |
| `measure <trial> <transcript.jsonl>` | reads the trial's transcript, worktree, and gate into `.baseline-runs/<trial>/metrics.json` |
| `record <trial>` | copies those metrics, minus machine-local paths, into `results/<trial>.json` to commit |

Trials are subagents of an orchestrating session, never headless agents.
