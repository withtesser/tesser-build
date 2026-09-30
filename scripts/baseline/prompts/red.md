You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
execute is in that worktree — use absolute paths, and `cd {worktree}` at the
start of each shell command. Its tools are on PATH through {venv}/bin (prefix
commands with `source {venv}/bin/activate &&`). No human will answer
questions: make each decision yourself and keep going. Do not spawn
subagents.

Task: write the **red acceptance test** for the user story in
`story-drafting/README.md`, in the `story-drafting/` app tree.

**Do not read, list, or inspect anything before you generate.** This prompt is
complete: the user story, the generator's spec reference, what the generated
tree looks like, and every command you need are all below. Your first tool
call writes the spec and generates. The worktree holds only the scaffold, and
nothing else in it bears on your two decisions.

The work is two decisions, and the rest is mechanical:

1. **The spec.** Model the user story's domain as a generator spec — the
   bounded context, the aggregate and its fields, and the name of every
   operation — in the README's own language. Write it to `{spec}` and
   generate the tree straight into `story-drafting/`.
2. **The acceptance test.** Decide how the user story's *then* shows over the
   host's protocol — what the read answers, and when — and write it as the
   root test `story-drafting/tests/test_acceptance.py`, replacing the one the
   generator wrote (the generate command prints it for you).

Done means all of these hold:

1. The acceptance test is a root test: it drives the app only through the
   running host, speaking the app's protocol, as the README's constraints say.
2. `scripts/verify story-drafting` gets past tessercheck with zero findings and
   past `mypy --strict`. Its pytest step fails.
3. The acceptance test fails at the user story's **then**. Submitting a JTBD
   through the host succeeds and results are read back through the host. It
   must not fail before that: not on a host operation that isn't implemented,
   an import or collection error, a missing module, or a host or Restate
   server that isn't running.
4. The tree holds the structure a submitted JTBD goes through — the client,
   the service, the durable workflow on Restate, the host, and what the
   component wires for them — but not the user story's behavior: a
   submitted JTBD has no status yet.

## The user story

{{FILE:story-drafting/README.md}}

## The generator

{{FILE:generator/README.md}}

## What a generated http handler answers

The `library` spec above generates this handler behind its routes,
`loans/adapters/handlers/http.py`; yours is the same with your spec's names:

```python
{{EXAMPLE:library/loans/adapters/handlers/http.py}}
```

## The harness

- The spec's `[environment_variables]` is `restate_ingress_url =
  "RESTATE_INGRESS"`; use `host = "http"` and `storage = "memory"`.
- Generate with
  `cd {worktree}/generator && PYTHONPATH=.:../tesser-py python3 -m srv.cli.generate {spec} {worktree}/story-drafting --print tests/test_acceptance.py`.
  It prints the path of every file it wrote, then the generated root test
  `tests/test_acceptance.py` verbatim — the file you replace with your
  acceptance test, so you have it without reading it back. The README
  already in `story-drafting/` stays.
- Run `scripts/verify` once, keeping its whole output, like this:

  ```sh
  cd {worktree} && RESTATE_INGRESS={ingress} RESTATE_ADMIN={admin} STORY_DRAFTING_PORT={port} \
    scripts/verify story-drafting > {log} 2>&1; echo "exit $?"
  grep -E '^(===|  →|  PASS|  FAIL)' {log}; tail -n 40 {log}
  ```

  It runs its steps in order and stops at the first that fails, printing a
  `  →` line as each step starts: tessercheck, `mypy --strict`, the non-root
  tests, then it serves `srv/http/main.py` on port {port}, registers its
  Restate endpoint, and runs `tests/` with the host's address passed as
  pytest's `--host` option (the root tests take it as the `host` fixture). Every step before the last `  →` line passed. The
  full output stays in `{log}` to grep; don't run it again to see more. Do
  not edit `scripts/verify`.
- Your Restate server is at ingress {ingress} and admin {admin}; generated
  tests that serve their own endpoints pick free ports themselves. Other
  agents work side by side on other ports: don't touch processes you didn't
  start. Work only inside the worktree.

When done, commit your work on the current branch with

```sh
cd {worktree} && git ls-files --modified --others --exclude-standard -z | xargs -0 git add -- \
  && git commit -q -m "<what you built>"
```

which stages every changed and new file by its path. Do not create worktrees
or branches, do not push, and do not open a pull request. Finish with a short
summary: the test's file and name, and the exact failure it produces.
