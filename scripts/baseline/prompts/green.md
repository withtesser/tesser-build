You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
run is in that worktree — use absolute paths, and `cd {worktree}` at the start
of each shell command. Its tools are on PATH through
{venv}/bin (prefix commands with `source {venv}/bin/activate &&`). No human
will answer questions: make each decision yourself and keep going. Do not
spawn subagents.

Task: make the **red acceptance test** for the story in
`story-drafting/README.md` pass, by building the story's behavior in the
`story-drafting/` app tree. The last commit on this branch added that test.

Done means all of these hold:

1. The acceptance test passes, and its assertions still say what they said in
   the last commit. You may change how it is set up, not what it checks.
2. `scripts/verify story-drafting` is green: tessercheck with zero findings,
   `mypy --strict`, and pytest.
3. You built what the story needs and nothing the README puts out of scope.

Follow the repo's `CLAUDE.md` and the `tesser-build` skill. You may extend the
tree's `run_story_drafting` arm in `scripts/verify`. A Restate server for this
tree is running at ingress http://localhost:38080 and admin
http://localhost:39070. Work only inside the worktree.

When done, commit your work on the current branch, staging files
individually. Do not create worktrees or branches, do not push, and do not open
a pull request. Finish with a short summary of what you built.
