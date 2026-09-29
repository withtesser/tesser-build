# tesser-build

A toolkit for building Python applications in the domain-driven design style
(value objects, entities, aggregates, application services, repositories,
bounded contexts), with the conventions **enforced by an analyzer in CI**
instead of just written down.

The bet behind it: consistently built domain objects make change cheaper,
because a change to a concept lands in one place instead of spreading across
every call site. That only holds if the conventions are applied every time.
So this repo ships them four ways at once:

- **an analyzer** (`tessercheck`) that checks a tree against them,
- **a runtime library** (`tesser`) whose base classes declare what each class is,
- **an agent skill** that teaches coding agents to build things this way,
- **executable examples**, kept at zero findings by CI.

MIT licensed (see `LICENSE`). Python **3.12+**.

## What's in the repo

Every top-level directory has a row in `manifest.json`, marked either `app`
(a tree with its own gates) or `ungated`.

| Path | What it is |
|---|---|
| [`tessercheck-py/`](tessercheck-py/) | The analyzer. It parses a tree without importing it and reports `TB0xx` findings. The full rule list is [`tessercheck-py/RULES.md`](tessercheck-py/RULES.md), which is generated from the implementation. |
| [`tessercheck-cli/`](tessercheck-cli/) | Console entry points packaged for use outside a checkout: `tessercheck-check`, the repairs `tessercheck-rename` and `tessercheck-mark`, and `tessercheck-hook` (a Claude Code `PostToolUse` hook). Ungated; `scripts/verify-packaging` tests it. |
| [`tesser-py/`](tesser-py/) | The `tesser` runtime library: the `ts.*` base classes (`ts.ValueObject`, `ts.AggregateRoot`, `ts.ApplicationService`, …). Subclassing one declares what a class is, and the analyzer checks the class against that declaration. |
| [`generator/`](generator/) | Writes a starting tesser app tree from a TOML spec (`generator/specs/*.toml`): one bounded context whose service runs a Restate workflow, whose orchestrator runs one action, and whose action writes to its store. The spec picks the store (`storage = "postgres"`, the default, or `"memory"`) and the host (`host = "cli"`, the default: a CLI host beside a Restate host; or `"http"`: one HTTP host serving the write and read routes with the Restate endpoint mounted at `/restate`), and how the write calls the workflow (`orchestrator.calling_mode = "run"`, the default: the write answers once the workflow has finished; or `"start"`: the write answers once the workflow has started). The output includes tests. |
| [`skills/tesser-build/`](skills/tesser-build/) | The agent skill. `SKILL.md` routes a task to per-concept guides (`value-objects.md`, `aggregates.md`, `repositories.md`, `testing.md`, `python.md`, …). You copy it into a consumer repo to use it. |
| [`examples/`](examples/) | Nine worked-example apps, each held to zero findings (see below). |
| [`layout/`](layout/) | An app that checks the repo layout. It fails when the directories on disk, `manifest.json`, the `.tesser-root` files, and the CI jobs disagree. |
| [`specs-app/`](specs-app/) | The product specification page and the service behind it, with a Playwright test. |
| [`docs/`](docs/) | Human docs: [`start-here.md`](docs/start-here.md), [`faq.md`](docs/faq.md), and the `design-*.md` files that explain each convention family. |
| [`scripts/`](scripts/) | `install-dev`, `verify`, `verify-packaging`. |

### The examples

| Example | Shows |
|---|---|
| `examples/python-app` | Reference template for a composition root and bounded contexts: two contexts (`campaign`, `linkpolicy`), one cross-context call, and one cross-context read. |
| `examples/minimal` | A small app that uses every tesser role in a conformant way: two contexts, kernels, `protocol`, `srv`, `app`. Durable kinds run on Restate and storage is Postgres. |
| `examples/durable-execution` | One context whose workflows run on Restate, behind a FastAPI host. |
| `examples/asyncpg` | The minimal shape backed by asyncpg repositories and a store that owns the transaction. Postgres only. |
| `examples/voice` | A `calls` context: a Restate orchestrator plus an asyncpg repository, with LiveKit at the edge. |
| `examples/ports` | Application ports: one context, two ports, an enum outcome, and a collection answer. |
| `examples/llmport` | A workflow whose next step is decided by an LLM tool call. |
| `examples/serdepy` | The serialization norm, covering every backing type. |
| `examples/errorspy` | The repository/service implementation that `skills/tesser-build/python.md` cites. |

## The conventions, briefly

The core is about value objects:

1. **Equality is by value, and the base class owns it.** A value object
   subclasses `ts.ValueObject`. Entities and aggregates don't get value
   equality.
2. **Every exported value object has an explicit equality test**
   (`test_*_equality`). This convention stands but isn't machine-enforced.
3. **The string form is for display, not equality.** `TB004` flags comparing
   two `str()` calls.

The analyzer enforces a lot more than that core:

- identity taxonomy
- serialization
- zero comments
- annotations
- function placement
- import direction for every module
- testing, e.g. hand-written fakes instead of mocking libraries, and exactly one sibling test file per module
- construction rules
- the application-service and durable-execution adapter types

Start with [`docs/start-here.md`](docs/start-here.md) for the concepts and
[`tessercheck-py/RULES.md`](tessercheck-py/RULES.md) for the exact rules.

Every gate requires zero findings. There is no ratchet and no way to switch
off a whole rule family. To excuse one finding, put a coded marker on the line
it applies to, e.g. `# tesser:debt TB052`. A marker that suppresses nothing is
itself a finding (`TB090`).

## Using it in your own repo

[`docs/start-here.md`](docs/start-here.md) lays out adoption in three steps:

1. **Docs.** Read `docs/start-here.md` and `docs/faq.md`.
2. **Skill.** Copy `skills/tesser-build/` into your repo so agents follow the
   conventions.
3. **CI.** Run the analyzer over your tree.

Your tree declares itself with a `.tesser-root` file at its root. The first
line is `app`; after that, only `skip <dir>`, `export <dir>`,
`import <package>`, and `stdlib <module>` lines are allowed. A missing or
malformed `.tesser-root` is a `TB044` finding.

**Running the analyzer from a checkout:**

```sh
cd tessercheck-py
PYTHONPATH=.:../tesser-py python3 -m srv.cli.main /path/to/your/tree
```

Exit code `0` means clean. Exit code `1` means findings, printed one per line
as `path:line: TB0xx <symbol> <specifics>; <rule>`.

**Running it from an install:** the packages aren't on PyPI. Install `tesser`,
`tessercheck-py`, and `tessercheck-cli` from git in a single `pip install`,
all pinned to the same rev, then run `tessercheck-check /path/to/tree`. The
exact command, and the setup for the Claude Code post-write hook, are in
[`tessercheck-cli/README.md`](tessercheck-cli/README.md).

**Generating a starting tree:**

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.generate specs/shop.toml /path/to/out
```

Two top-level spec keys choose the shape. `storage = "memory"` writes an
in-memory repository and no `pgdatabase` package, and takes no
`environment_variables.storage_url`; it needs `host = "http"`, because a CLI
host reads in a process of its own and would never see the store the served
Restate endpoint writes. `host = "http"` writes `srv/http/main.py` (a FastAPI
app: `POST /<collection>` and `GET /<collection>/{<identity>}`, the Restate
endpoint mounted at `/restate`), its `protocol/http.py`, an `HttpHandler`, and
a root acceptance test that reaches the served host through
`ts.served(...)`, reading its address from the variable named by
`environment_variables.host_url`. `specs/library.toml` is HTTP over memory,
`specs/helpdesk.toml` HTTP over Postgres.

The output directory may already hold files. A file the generator does not
write (a `README.md`, say) is kept beside the tree, and a file it would write
the same is fine; a file it would write differently is a problem, and then
nothing is written.

## Working on this repo

```sh
python3 -m venv .venv && source .venv/bin/activate
scripts/install-dev              # installs the requirements-dev.txt of examples/, layout/, tessercheck-py/, tesser-py/
scripts/verify                   # every gated tree listed in manifest.json
scripts/verify tessercheck-py    # or only the trees you touched
```

`scripts/verify` runs the same commands CI runs; the jobs in
`.github/workflows/test.yml` call it. It starts with the layout check, then
runs each tree's gates. The gates are tessercheck at zero findings,
`mypy --strict`, and `pytest`, and some trees add `ruff`, `import-linter`, or
more.

Things to know before running it:

- **Some trees need services.** `minimal`, `durable-execution`, `voice`,
  `asyncpg`, and `generator` need a local Postgres and/or Restate server; they
  have no skip. The `docker run` commands and default ports are in comments
  above each arm in `scripts/verify`.
- **Some trees need their own installs.** `install-dev` doesn't cover
  `generator/` or `specs-app/`, so install their `requirements-dev.txt`
  yourself. `specs-app` also needs a browser
  (`python -m playwright install chromium`).
- **The `tesser-py` gate runs the real mutmut CLI** (pinned `==3.7.0`). It's
  slower than the others, and it can fail because mutmut changed rather than
  because this repo did.
- **A change to one example can break the analyzer's gate.** The analyzer
  runs over every example tree, so a layout change in an example can break it
  even when nothing under `tessercheck-py/` changed.
- **`scripts/verify-packaging`** builds the three distributions, installs them
  into a clean virtualenv, and runs the installed commands.

Adding a top-level directory or an `examples/` subdirectory needs a row in
`manifest.json`, and the layout check fails without one. A new `app` row also
needs a `run_*` arm in `scripts/verify` and a CI job. If you change a
convention, update every place it's written down in the same change. The rules
for that are in [`docs/skill-authoring.md`](docs/skill-authoring.md).
Agent-specific guidance is in [`CLAUDE.md`](CLAUDE.md).
