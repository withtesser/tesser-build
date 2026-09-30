You are working alone in a git worktree of tesser-build that is already on
its own branch: {worktree}. Every file you read or write and every command you
execute is in that worktree — use absolute paths, and `cd {worktree}` at the
start of each shell command. Its tools are on PATH through {venv}/bin (prefix
commands with `source {venv}/bin/activate &&`). No human will answer
questions: make each decision yourself and keep going. Do not spawn
subagents.

Task: make the **red acceptance tests** of the `story-drafting` app pass, by
writing the behavior its stories need into the files that are yours.

**Do not read, list, or inspect anything before your first edit.** This prompt
is complete: the stories and their language, the contracts the generated code
relies on, every file you own as it stands, the acceptance tests, the
construction rules for your files, and every command you need are all below.

## What is yours, and what is not

The tree was rendered from its specs. Every file the generator owns carries a
generated mark; do not edit one — a drift check fails if you do. **Yours are:**

- `story-drafting/drafting/domain/jtbd.py` and its `test_jtbd.py`: the
  aggregate. Its contract — the spec it is constructed from, its commands and
  the outcomes they answer, and what can be read from it — is fixed by the
  composition below and must not change. Everything inside is yours: value
  objects, private fields, validation, defaults, and how each read is
  computed. You may add domain modules (each with its sibling test) for the
  value objects and entities you model.
- `story-drafting/drafting/adapters/gateways/template_story_drafter.py` and
  its `test_template_story_drafter.py`: the body of the one implementation
  the toolkit does not supply.

Do not edit the specs (generator/compositions/story-drafting/), the acceptance tests, `scripts/verify`, or any
`.tesser-root` (no `skip` lines).

**If the contract lacks something you need** — a field, an outcome, a read,
an operation — do not add it and do not work around it. Stop, commit what you
have, and report it as a GAP in your summary: what you needed, and for which
story. A missing piece of the contract is a defect in the composition, fixed
there, not in your files.

## The language

```toml
{{FILE:generator/compositions/story-drafting/language.toml}}
```

## The stories

```toml
{{FILE:generator/compositions/story-drafting/story.toml}}
```

## The contracts (composition)

```toml
{{FILE:generator/compositions/story-drafting/composition.toml}}
```

## The implementations

```toml
{{FILE:generator/compositions/story-drafting/implementations.toml}}
```

## The acceptance tests (they must pass unchanged)

```python
{{FILE:story-drafting/tests/test_submitting_jtbds.py}}
```

```python
{{FILE:story-drafting/tests/test_reading_jtbds_by_jtbd_id.py}}
```

## Your files as they stand

```python
{{FILE:story-drafting/drafting/domain/jtbd.py}}
```

```python
{{FILE:story-drafting/drafting/domain/test_jtbd.py}}
```

```python
{{FILE:story-drafting/drafting/adapters/gateways/template_story_drafter.py}}
```

```python
{{FILE:story-drafting/drafting/adapters/gateways/test_template_story_drafter.py}}
```

## How your files are built (from the tesser-build skill)

{{SECTION:skills/tesser-build/python.md#Value objects}}

{{SECTION:skills/tesser-build/python.md#Entities}}

{{SECTION:skills/tesser-build/python.md#Aggregates}}

{{SECTION:skills/tesser-build/python.md#Outcomes}}

{{FILE:skills/tesser-build/testing.md}}

## The harness

- Run the gate like this, keeping its whole output:

  ```sh
  cd {worktree} && RESTATE_URL={engine_url} RESTATE_ADMIN={admin} STORY_DRAFTING_PORT={port} \
    scripts/verify story-drafting > {log} 2>&1; echo "exit $?"
  grep -E '^(===|  →|  PASS|  FAIL)' {log}; tail -n 40 {log}
  ```

  It runs its steps in order and stops at the first that fails: tessercheck,
  `mypy --strict`, the non-root tests, then it serves the host on port {port}
  and runs the acceptance tests against it. Grep `{log}` rather than running
  it again to see more.
- For a quick check while you work, run just your own tests:
  `cd {worktree}/story-drafting && PYTHONPATH=.:../tesser-py pytest -q drafting/domain drafting/adapters/gateways`.
- Your Restate server's URL is {engine_url} and its admin API {admin}; serve hosts
  only on ports {port}–{port_last}. Other agents work side by side: don't
  touch processes you didn't start. Work only inside the worktree.

Done means `scripts/verify story-drafting` is green — tessercheck with zero
findings, `mypy --strict`, and every test tier — with the acceptance tests
unchanged and only your files changed.

When done, commit your work on the current branch with

```sh
cd {worktree} && git ls-files --modified --others --exclude-standard -z | xargs -0 git add -- \
  && git commit -q -m "<what you built>"
```

Do not create worktrees or branches, do not push, and do not open a pull
request. Finish with a short summary: what you modeled in the domain, what
the drafter produces, and any GAP.
