You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
run is in that worktree — use absolute paths, and `cd {worktree}` at the start
of each shell command. Its tools are on PATH through
{venv}/bin (prefix commands with `source {venv}/bin/activate &&`). No human
will answer questions: make each decision yourself and keep going. Do not
spawn subagents.

Task: write the **red acceptance test** for the story in
`story-drafting/README.md`, in the `story-drafting/` app tree.

Done means all of these hold:

1. The acceptance test exists and drives the app only through its public
   client, as the README's constraints say.
2. `scripts/verify story-drafting` gets past tessercheck with zero findings and
   past `mypy --strict`. Its pytest step fails.
3. The acceptance test fails **because the story's behavior is not built** — an
   assertion failure, or the app answering that the operation is not
   implemented. It must not fail from an import error, a collection error, a
   missing module, or a service that is not running.
4. You have not built the story's behavior. Build only the structure the test
   needs to import, run, and reach the missing behavior.

Follow the repo's `CLAUDE.md` and the `tesser-build` skill. You may extend the
tree's `run_story_drafting` arm in `scripts/verify` (for example to serve and
register the Restate endpoint, as `run_durable_execution` does). A Restate
server for this tree is running at ingress http://localhost:38080 and admin
http://localhost:39070. Work only inside the worktree.

When done, commit your work on the current branch, staging files
individually. Do not create worktrees or branches, do not push, and do not open
a pull request. Finish with a short summary: the test's file and name, and the
exact failure it produces.
