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
- any other file under "Your files as they stand" below: a body the toolkit
  does not supply, such as a gateway the composition implements with
  `body = "agent"`.
- the agent-owned STORE class that `implementations.toml` declares
  (`body = "agent"` on the repository port) and its sibling test, under
  `story-drafting/drafting/adapters/repositories/`: it starts as a working
  in-memory store. Make it keep its data in the storage `infra.toml` declares
  for it (for `sqlite`: the database file whose path the class is built with as
  `location`, using the standard library's `sqlite3`), so the data survives the
  process. Keep its public shape (`transaction()`, the repository operations),
  which the generated code relies on. Stories that say a job to be done
  survives a restart of the service are yours to satisfy here.

Do not edit the specs (story-drafting/specs/), the acceptance tests, `scripts/verify`, or any
`.tesser-root` (no `skip` lines).

**If the contract lacks something you need** — a field, an outcome, a read,
an operation — do not add it and do not work around it. Stop, commit what you
have, and report it as a GAP in your summary: what you needed, and for which
story. A missing piece of the contract is a defect in the composition, fixed
there, not in your files.

## The language

```toml
{{FILE:story-drafting/specs/language.toml}}
```

## The stories

```toml
{{FILE:story-drafting/specs/story.toml}}
```

## What it runs on

```toml
{{FILE:story-drafting/specs/infra.toml}}
```

## The contracts (composition)

```toml
{{FILE:story-drafting/specs/composition.toml}}
```

## The implementations

```toml
{{FILE:story-drafting/specs/implementations.toml}}
```

## The acceptance tests (they must pass unchanged)

```python
{{FILE:story-drafting/tests/test_submitting_jtbds.py}}
```

```python
{{FILE:story-drafting/tests/test_reading_jtbds_by_jtbd_id.py}}
```

## Your files as they stand

Every file in the tree that carries no generated mark, outside the acceptance tests.

{{AGENT_FILES}}

## How your files are built (from the tesser-build skill)

{{SECTION:skills/tesser-build/python.md#Value objects}}

{{SECTION:skills/tesser-build/python.md#Entities}}

{{SECTION:skills/tesser-build/python.md#Aggregates}}

{{SECTION:skills/tesser-build/python.md#Outcomes}}

{{FILE:skills/tesser-build/testing.md}}

## The harness

- "The service has been restarted" (story s-3) means: its process is stopped and started again with the same command and environment, while the Restate server keeps running. No acceptance test here restarts it; the runner does.
- Run the gate like this, keeping its whole output:

  ```sh
  source {venv}/bin/activate && cd {worktree} && scripts/verify story-drafting > {log} 2>&1; echo "exit $?"
  grep -E '^(===|  →|  PASS|  FAIL)' {log}; tail -n 40 {log}
  ```

  It runs its steps in order and stops at the first that fails: the render
  check, tessercheck, `mypy --strict`, then one plain `pytest` over every
  tier. The tests own their infrastructure: the rendered root `conftest.py`
  starts private Restate engines and serves the host for the acceptance
  tests. Grep `{log}` rather than running it again to see more.
- For a quick check while you work, run just your own tests: `cd
  {worktree}/story-drafting && pytest -q <your test files>`.
- Other agents work side by side: don't touch processes you didn't start.
  Work only inside the worktree.

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
