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

1. The acceptance test exists as a root test and drives the app only through
   a running host, speaking the app's protocol, as the README's constraints
   say.
2. `scripts/verify story-drafting` gets past tessercheck with zero findings and
   past `mypy --strict`. Its pytest step fails.
3. The acceptance test fails at the story's **then**. Starting a run through
   the host succeeds and results are read back through the host. It must not
   fail before that: not on a host operation that isn't implemented, an import
   or collection error, a missing module, or a host or Restate server that
   isn't running.
4. You have built the structure the story's run goes through — the client, the
   service, the durable workflow on Restate, the host, and what the component
   wires for them — but not the story's behavior: no drafting, and no waiting for the
   pick.

Follow the repo's `CLAUDE.md` and the `tesser-build` skill. You may extend the
tree's `run_story_drafting` arm in `scripts/verify` (to serve and register the
hosts the root tier drives, as `run_durable_execution` does); keep taking the
Restate server and host ports from the environment as it does now, and after
editing `scripts/verify` diff it and confirm only `run_story_drafting` changed.
Your Restate server is at ingress {ingress} and admin {admin}; serve hosts only
on ports {port}–{port_last}. Run the gate as
`RESTATE_INGRESS={ingress} RESTATE_ADMIN={admin} STORY_DRAFTING_PORT={port} scripts/verify story-drafting`.
Other agents run side by side on other ports: don't touch processes you
didn't start. Paid APIs are allowed. Work only inside the worktree.

When done, commit your work on the current branch, staging files
individually. Do not create worktrees or branches, do not push, and do not open
a pull request. Finish with a short summary: the test's file and name, and the
exact failure it produces.
