You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
execute is in that worktree — use absolute paths, and `cd {worktree}` at the
start of each shell command. Its tools are on PATH through {venv}/bin (prefix
commands with `source {venv}/bin/activate &&`). No human will answer
questions: make each decision yourself and keep going. Do not spawn
subagents.

Task: design the `{tree}` app from its specs, generate it, and write
its **red acceptance tests**.

**Do not read, list, or inspect anything before you generate.** This prompt is
complete: the language and the stories, the spec formats, a worked example of
each spec and of what the generator renders, and every command you need are
all below. Your first tool call writes the specs and renders. The worktree
holds only the scaffold, and nothing else in it bears on your two decisions.

The work is two decisions, and the rest is mechanical:

1. **The composition.** From the language and the stories, decide the pieces
   and how they connect, and write `{tree}/specs/composition.toml`;
   say which implementation satisfies each contract in each environment in
   `{tree}/specs/implementations.toml`; give sample values in
   `{tree}/specs/generator.toml`. Every name comes from the language
   (a term's code name or a convention word). Every piece names the stories it
   serves, and every level-1 and level-2 story is served. Write down only what
   is a decision: nothing a convention derives, and no behavior — what the
   domain does inside is the green agent's, so the aggregate appears only as
   its contract. Then render the tree straight into `{tree}/`.
2. **The acceptance tests.** The render writes one root test skeleton per
   level-2 story with a route, named for the route
   (for example `tests/test_submitting_loans.py` for a `POST /loans`): it reaches the
   served host, calls the route, asserts its status, and carries two
   placeholders that quote the story's words: its *given* (before the call)
   and its *then* (after it). Replace the *given* placeholder with what
   puts the system in the state the story's *given* describes, through the
   running host, and bind any value the route needs; replace the *then*
   placeholder with assertions of exactly that story's *then* and nothing
   more. The render command below prints every skeleton, so you have them
   without reading them.

Done means all of these hold:

1. `scripts/verify {tree}` gets past tessercheck with zero findings
   and past `mypy --strict`, and in its pytest every test passes except
   acceptance tests in `tests/`.
2. At least one acceptance test fails, and every one that fails fails at its
   story's **then**: the host answers, and what it answers is the generated
   stubs' placeholder behavior. A test whose *then* the stubs already satisfy
   passes; don't weaken or distort a test to make it fail. None fails before
   its *then*: not on an operation that isn't implemented, an import or
   collection error, a missing module, or a host that was not served.
3. Every level-1 and level-2 story in `story.toml` is served by some piece in
   `composition.toml`, and every piece serves at least one story.

## The language

```toml
{{FILE:{tree}/specs/language.toml}}
```

## The stories

```toml
{{FILE:{tree}/specs/story.toml}}
```

## What it runs on (given: the engineer's decisions, not yours)

```toml
{{FILE:{tree}/specs/infra.toml}}
```

You do not write or change `infra.toml`. Its `[storage.*]` are the stores that
exist: every store port you declare must be implemented by one of them, as
`[implementations.<Port>.<storage>]`, and a storage that is not `memory` is
implemented by an agent-owned class you name (`body = "agent"`, `class = ...`;
the green agent writes its body). A story that says data must survive a restart
needs a storage that keeps it.

## The spec formats

{{FILE:generator/compositions/README.md}}

## A worked example: the library composition

A different domain, written in the same formats. Its `composition.toml`:

```toml
{{FILE:generator/compositions/library/composition.toml}}
```

Its `implementations.toml`:

```toml
{{FILE:generator/compositions/library/implementations.toml}}
```

It renders this handler behind its routes; yours is the same with your
composition's names:

```python
{{EXAMPLE:library/loans/adapters/handlers/http.py}}
```

## The harness

- If a story says "the service has been restarted", that means its process is stopped and started again with the same command and environment, while the durable-execution engine keeps running. No acceptance test here can restart the service; the runner does.
- Render with
  `cd {worktree}/generator && PYTHONPATH=.:../tesser-py python3 -m srv.cli.render {worktree}/{tree}/specs {worktree}/{tree} --print 'tests/test_*.py'`.
  It prints the path of every file it wrote, then each skeleton verbatim. The
  specs already in `{tree}/` stay. If the render
  reports a problem, it writes nothing: fix the spec it names and render
  again.
- Run `scripts/verify` once, keeping its whole output, like this:

  ```sh
  source {venv}/bin/activate && cd {worktree} && scripts/verify {tree} > {log} 2>&1; echo "exit $?"
  grep -E '^(===|  →|  PASS|  FAIL)' {log}; tail -n 40 {log}
  ```

  It runs its steps in order and stops at the first that fails, printing a
  `  →` line as each step starts: the render check, tessercheck,
  `mypy --strict`, then one plain `pytest` over every tier. The tests own
  their infrastructure: the rendered root `conftest.py` starts private Restate
  engines, and its `host` fixture serves `srv/http/main.py` on a free port and
  registers it, so an acceptance test asks for `host` and gets its address.
  Every step before the last `  →` line passed. The full output stays in
  `{log}` to grep; don't run it again to see more. Do not edit
  `scripts/verify`.
- Other agents work side by side: don't touch processes you didn't start.
  Work only inside the worktree. Do not add `skip` lines to any
  `.tesser-root`.

When done, commit your work on the current branch with

```sh
cd {worktree} && git ls-files --modified --others --exclude-standard -z | xargs -0 git add -- \
  && git commit -q -m "<what you built>"
```

which stages every changed and new file by its path. Do not create worktrees
or branches, do not push, and do not open a pull request. Finish with a short
summary: each acceptance test's file and name, the exact failure each
produces, and any decision in the composition you were least sure of.
