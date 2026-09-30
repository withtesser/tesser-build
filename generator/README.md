# generator

Writes a starting tesser app tree from a TOML spec: one bounded context whose
client writes and reads one aggregate. The write goes through the context's
service to a Restate workflow, whose orchestrator runs one action, whose
action saves the aggregate to its store; the read loads it back. Every module
comes with its sibling test, and the tree gets a user-facing host and a root
acceptance test that drives that host. The output passes tessercheck with zero
findings, `mypy --strict`, and its own tests.

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.generate <spec.toml> <out_dir> [--print <path>]...
```

It exits 0 and lists the files it wrote, or exits 1 and lists every problem
with the spec and writes nothing.

**`--print <path>`** names a file to print back, by its path relative to the
output directory as the list prints it (`--print tests/test_acceptance.py`).
It repeats, and the files print in the order named: after the list, each gets
a blank line, a header line `--- <path>`, and its content as written. A path
the tree does not write is a problem (`--print names <path>, which the
generator does not write`), so nothing is written. Without `--print` the
output is the list alone.

**The output directory** may already hold files. A file the generator does not
write (a `README.md`, say) is kept beside the tree; a file it would write the
same is fine; a file it would write differently is a problem.

## The spec

Every key is required unless the table says otherwise. *snake_case* is
`[a-z][a-z0-9]*` words joined by `_`; an *operation* is snake_case of at least
two words, a verb and a noun (`place_call`).

| Key | Shape | Becomes |
|---|---|---|
| `app_name` | snake_case | the app (`app/app.py`, the `App` class) |
| `bounded_context_name` | snake_case, not a reserved name | the context package |
| `aggregate_root_class_name` | PascalCase | the aggregate root class; its module is the snake_case form |
| `durable_execution_engine` | `"restate"` | the one engine with templates |
| `storage` | `"postgres"` (default) or `"memory"` | an asyncpg repository and a `pgdatabase` package, or an in-memory store |
| `host` | `"cli"` (default) or `"http"` | a CLI host plus a separate Restate endpoint, or one FastAPI process serving the routes with the Restate endpoint at `/restate` |
| `identity_field_name` | snake_case | the aggregate's identity field (always `str`) |
| `identity_port_operation_name` | operation | the identity port's operation (`issue_call_id`) |
| `[aggregate_fields]` | `name = "str"` or `"int"`, at least one | the aggregate's fields, each a value object |
| `[sample_values]` | `name = [a, b]` for the identity and every field | two distinct values per field, used in the generated sibling tests |
| `client.write_operation_name` | operation | the client's write |
| `client.read_operation_name` | operation | the client's read |
| `client.read_response_fields` | identity and field names | what the read answers, in order |
| `orchestrator.operation_name` | operation | the workflow's operation |
| `orchestrator.calling_mode` | `"run"` (default) or `"start"` | how the service calls the orchestrator relay: `run_<operation>` or `start_<operation>` |
| `action.operation_name` | operation | the one action the orchestrator runs |
| `repository.save_operation_name`, `.load_operation_name` | operation | the repository port's two operations |
| `repository.load_response_collection_name` | snake_case | the collection name (the table, and the http route `/<collection>`) |
| `acceptance_test.test_class_name` | `Test` + PascalCase | the root acceptance test's class |
| `acceptance_test.test_method_name` | `test_` + snake_case | its method |
| `acceptance_test.asserted_field` | an aggregate field the read answers | the field it asserts is read back |
| `acceptance_test.random_values` | values of that field's type | the values it picks from at random |
| `environment_variables.restate_ingress_url` | UPPER_CASE | the variable the app reads the Restate ingress from |
| `environment_variables.storage_url` | UPPER_CASE; postgres only | the variable the app reads its database from |

**Refused up front:**

- `storage = "memory"` with `host = "cli"`: a CLI host reads in a process of
  its own and would never see the store the served Restate endpoint writes.
- A bounded context or field named `adapters`, `app`, `application`, `client`,
  `component`, `config`, `conftest`, `domain`, `identity`, `pgdatabase`,
  `protocol`, `spec`, `srv`, or `tests`.
- Two operations with the same name.
- An operation beginning with `start_`, `run_`, or `await_`: those are relay
  calling modes (TB085), and no client, port, or orchestrator operation may
  begin with one. When the domain's own verb is one of them, name the act
  without it (`begin_run`).
- Sample and random values that are not printable ASCII free of quotes and
  backslashes (identity values: letters, digits, `.`, `_`, `~`, `-`).

## What `host = "http"` serves

- `POST /<collection>` with a JSON body of the aggregate's fields: 201 and
  `{"<identity>": "..."}`.
- `GET /<collection>/{<identity>}`: 200 and the read response fields as JSON;
  an unknown identity answers 500.
- The Restate endpoint at `/restate`, in the same process.

With `orchestrator.calling_mode = "run"` (the default), the write waits for
the workflow to finish (the service calls the orchestrator relay's `run_`
operation), so a read right after the write sees the saved aggregate. With
`"start"`, the write answers as soon as the workflow is started, and a read
right after it can answer 500 until the action has saved the aggregate.

## Picking a calling mode

- **`run`**: the write answers after the workflow finishes, so a read right
  after the write sees the aggregate. Pick it when the workflow finishes
  quickly and on its own.
- **`start`**: the write answers once the workflow is started. Pick it for a
  workflow that goes on without the caller, like one that waits on a person or
  a durable promise, where a write that waited would not return. The client
  comes back to read later. The relay's operation is `start_<operation>`,
  answered by a `Start<Operation>Response` that carries the identity; the
  Restate dispatcher sends with `workflow_send` instead of `workflow_call`;
  and the root acceptance test retries its read until it answers (30 seconds,
  0.2 seconds apart).

## Example: HTTP over memory

`specs/library.toml`:

```toml
app_name = "library"
bounded_context_name = "loans"
aggregate_root_class_name = "Loan"
durable_execution_engine = "restate"
storage = "memory"
host = "http"
identity_field_name = "loan_id"
identity_port_operation_name = "issue_loan_id"

[aggregate_fields]
borrower_name = "str"
days = "int"

[sample_values]
loan_id = ["loan-1", "loan-2"]
borrower_name = ["Ada", "Grace"]
days = [7, 14]

[client]
write_operation_name = "lend_book"
read_operation_name = "get_loan"
read_response_fields = ["loan_id", "borrower_name", "days"]

[orchestrator]
operation_name = "arrange_loan"

[action]
operation_name = "record_loan"

[repository]
save_operation_name = "save_loan"
load_operation_name = "load_loan"
load_response_collection_name = "loans"

[acceptance_test]
test_class_name = "TestLendingBooks"
test_method_name = "test_a_lent_book_is_read_back_with_its_days"
asserted_field = "days"
random_values = [7, 14, 21, 28]

[environment_variables]
restate_ingress_url = "RESTATE_INGRESS"
```

Every spec in `specs/` is gated: `scripts/verify generator` generates each one
and runs the generated tree's own gates.

## Rendering a composition

The second entry point renders a tree from a composition directory (the six
spec formats of `compositions/<name>/`, read in order: `language.toml`,
`story.toml`, `infra.toml`, `composition.toml`, `implementations.toml`,
`generator.toml`) instead of a fixed-shape spec:

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.render <composition-dir> <out-dir>
```

`compositions/README.md` is the reference: every key each format takes, what
the renderer derives, what it renders, and which rendered files are the
agent's.

`infra.toml` holds what the app runs on and what an operator must provide: the
app, the runtime, the engine (with `engine_path` and its variables), the host,
each storage (`[storage.<name>]`, with the `location_variable` that locates it,
for every storage but `memory`), and the variables. `implementations.toml`
holds only the port-level mapping (`[implementations]` and `[environments]`);
one that still carries `app`, `[engine]`, `[hosts]`, or `[variables]` is a
problem saying they moved.

A port in `implementations.toml` with `body = "agent"` and a `class` renders an
agent-owned stub: a gateway for a gateway port, and, for a store port (one that
carries the aggregate), a store under `<context>/adapters/repositories/` that
starts as a working in-memory store, so an agent can swap in a durable body
(a file, SQLite) inside its own file without touching a generated one. A store
port's implementation key names a storage `infra.toml` declares; when that
storage has a `location_variable`, the app reads it at load, the component
passes it to the store as `location: str`, and the stub takes it and ignores it
until the agent writes the durable body.

The composition holds only what current stories require: every enum value,
client operation request and response field, aggregate read, signal payload
field, and non-success command outcome (the success outcome is the first one
listed) must be named, as a whole word, in a story's given, when, or then. A
piece no story names is a problem that says which piece, and the fix is to write
it in a story or remove it from the composition (`compositions/README.md`).

A render answers these as problems (exit 1, nothing written) rather than
crashing or rendering something broken: a path naming one `{field}` twice, and a
sample list in `generator.toml` with no values (`borrower = []`). A root test
skeleton is named for its method and every path segment, a parameter as
`by_<field>` (`GET /loans` is `test_reading_loans.py`, `GET /loans/{loan_id}` is
`test_reading_loans_by_loan_id.py`), and holds two placeholders the agent
writes: the story's given (how the host reaches it, and any path value the
route needs) and its then. A story file with `reached_by` is a problem: the
key is no longer part of the format. A path parameter for an `int` field answers
400 unless it is an integer (an optional `-` and at most 18 ASCII digits). A
command with `takes = {}` renders a `<Command>Spec` whose constructor is `pass`.
`scripts/verify` stops a served host only while it is the process it started
(same start time), never signalling one that has already exited.

Every composition in `compositions/` is gated: `scripts/verify
generator` renders each one and runs the rendered tree's tessercheck,
`mypy --strict`, and every test tier but the root, with every storage
`location_variable` its `infra.toml` declares set to a fresh temporary path.
