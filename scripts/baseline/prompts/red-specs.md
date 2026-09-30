You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
execute is in that worktree — use absolute paths, and `cd {worktree}` at the
start of each shell command. Its tools are on PATH through {venv}/bin (prefix
commands with `source {venv}/bin/activate &&`). No human will answer
questions: make each decision yourself and keep going. Do not spawn
subagents.

Task: design the `story-drafting` app from its specs, generate it, and write
its **red acceptance tests**.

**Do not read, list, or inspect anything before you generate.** This prompt is
complete: the language and the stories, the spec formats, a worked example of
each spec and of what the generator renders, and every command you need are
all below. Your first tool call writes the specs and renders. The worktree
holds only the scaffold, and nothing else in it bears on your two decisions.

The work is two decisions, and the rest is mechanical:

1. **The composition.** From the language and the stories, decide the pieces
   and how they connect, and write `story-drafting/specs/composition.toml`;
   say which implementation satisfies each contract in each environment in
   `story-drafting/specs/implementations.toml`; give sample values in
   `story-drafting/specs/generator.toml`. Every name comes from the language
   (a term's code name or a convention word). Every piece names the stories it
   serves, and every level-1 and level-2 story is served. Write down only what
   is a decision: nothing a convention derives, and no behavior — what the
   domain does inside is the green agent's, so the aggregate appears only as
   its contract. Then render the tree straight into `story-drafting/`.
2. **The acceptance tests.** The render writes one root test skeleton per
   level-2 story with a route, named for the route
   (`story-drafting/tests/test_submitting_jtbds.py` for `POST /jtbds`,
   `test_reading_jtbds.py` for the read route): it reaches the
   served host, reaches the story's *given* as its `reached_by` says, calls
   the route, asserts its status, and ends in one placeholder assertion
   carrying the story's *then*. Replace each placeholder with assertions of
   exactly that story's *then* and nothing more. The render command below
   prints both skeletons, so you have them without reading them.

Done means all of these hold:

1. `scripts/verify story-drafting` gets past tessercheck with zero findings,
   past `mypy --strict`, and past every test tier but the root. Its root tier
   fails.
2. At least one acceptance test fails, and every one that fails fails at its
   story's **then**: the host answers, and what it answers is the generated
   stubs' placeholder behavior. A test whose *then* the stubs already satisfy
   passes; don't weaken or distort a test to make it fail. None fails before
   its *then*: not on an operation that isn't implemented, an import or
   collection error, a missing module, or a host or Restate server that isn't
   running.
3. Every level-1 and level-2 story in `story.toml` is served by some piece in
   `composition.toml`, and every piece serves at least one story.

## The language

```toml
{{FILE:story-drafting/specs/language.toml}}
```

## The stories

```toml
{{FILE:story-drafting/specs/story.toml}}
```

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

- Render with
  `cd {worktree}/generator && PYTHONPATH=.:../tesser-py python3 -m srv.cli.render {worktree}/story-drafting/specs {worktree}/story-drafting --print tests/test_submitting_jtbds.py --print tests/test_reading_jtbds.py`.
  It prints the path of every file it wrote, then each skeleton verbatim. The
  README and the specs already in `story-drafting/` stay. If the render
  reports a problem, it writes nothing: fix the spec it names and render
  again.
- Run `scripts/verify` once, keeping its whole output, like this:

  ```sh
  cd {worktree} && RESTATE_INGRESS={ingress} RESTATE_ADMIN={admin} STORY_DRAFTING_PORT={port} \
    scripts/verify story-drafting > {log} 2>&1; echo "exit $?"
  grep -E '^(===|  →|  PASS|  FAIL)' {log}; tail -n 40 {log}
  ```

  It runs its steps in order and stops at the first that fails, printing a
  `  →` line as each step starts: tessercheck, `mypy --strict`, the non-root
  tests, then it serves `srv/http/main.py` on port {port}, registers its
  Restate endpoint, and runs `tests/` with the host's address in
  `STORY_DRAFTING_HOST`. Every step before the last `  →` line passed. The
  full output stays in `{log}` to grep; don't run it again to see more. Do
  not edit `scripts/verify`.
- Your Restate server is at ingress {ingress} and admin {admin}; generated
  tests that serve their own endpoints pick free ports themselves. Other
  agents work side by side on other ports: don't touch processes you didn't
  start. Work only inside the worktree. Do not add `skip` lines to any
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
