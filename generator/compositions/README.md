# Compositions: the five spec formats `srv.cli.render` reads

A composition is a directory holding five TOML files. `srv.cli.render` reads them
and writes a complete tesser app tree:

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.render <composition-dir> <out-dir>
```

It prints the path of every file it wrote, one per line (then `kept <path>` for
each agent-owned file it left alone), and exits 0; or it prints every problem
on stderr as `render: <problem>`, exits 1, and writes nothing.

**The output directory** may already hold files. A file the renderer does not
write (a `README.md`, a `specs/` directory holding the composition itself) is
left where it is. A file it would write the same is written again. A file it
would write differently is a problem, and nothing is written, with one
exception: an agent-owned file (below) that already exists is kept as it is.

Every directory in `generator/compositions/` is gated: `scripts/verify
generator` renders it and runs the rendered tree's tessercheck (zero findings),
`mypy --strict`, and every test tier but the root. `library/` is the small
worked example.

**Not rendered yet** (a composition that uses one is refused, with the reason):
`[shapes]`, `[messages]`, `[enums]`, list types, and `[aggregate.commands]`
(with `commands` and `calls_on` on an action). Every read must be a spec field
of the same type.

## Which file answers which question

| File | Question | Written by |
|---|---|---|
| `language.toml` | What do our words mean? | the product owner, with the agent |
| `story.toml` | What must a user be able to observe? | the product owner |
| `composition.toml` | Which pieces exist and how do they connect? The contracts only. | the agent, reviewed |
| `implementations.toml` | What satisfies each contract, in which environment? | a tech lead, reviewed |
| `generator.toml` | Sample values for the generated tests, and nothing a reviewer cares about. | anyone |

Each fact lives in one file. `composition.toml` never says what implements a
contract; `implementations.toml` never declares a contract. Every name in
`composition.toml` is a code name from `language.toml` (a snake_case field or
operation, a PascalCase type) or a word the conventions derive (below).

## Types

A field's type is one of:

- `"str"` or `"int"`
- the aggregate's snake_case name (`loan` for `Loan`), only in a port
  operation: the whole aggregate as its port record.

**Where a field's type comes from.** A field is named by its bare name in
every list (`request = ["loan_id", "borrower"]`). Its type is looked up, in
order: the aggregate's `[aggregate.spec]`,
then `[aggregate.reads]`.
Every field named anywhere must get a type this way.

## 1 `language.toml`

Read only to check it is TOML; everything in it is for people. Its shape (as in
`library/language.toml`): `context = "<context>"`, then `[[terms]]` tables with
`term`, `means`, `code_names = [...]`, and optionally `short`, `status`, `not`,
`note`, and a `[conventions]` table. Write it first: every other file uses its
code names.

## 2 `story.toml`

A tree of JTBDs and stories. The renderer reads two things from it: story ids,
and each served level-2 story's `when` and `then`.

```toml
[[jtbds]]                         # level 1, in the user's words
id = "j-root"
level = 1
as = "..."                        # informational
i_want = "..."
so_that = "..."

[[jtbds.stories]]
id = "s-1"
given = "..."
when = "..."
then = "..."

[[jtbds.stories.jtbds]]           # level 2: the interface
id = "j-1-a"
level = 2

[[jtbds.stories.jtbds.stories]]
id = "s-1-a-1"
given = "a borrower and a title"
when = "I POST them as JSON to /loans"          # the method, then the path
then = "I get back 201 with its loan_id"        # "get back <status>"
reached_by = "..."                              # optional, for the acceptance test's given
```

A level-2 story an HTTP route serves names the method (`GET`, `POST`, `PUT`,
`PATCH`, `DELETE`) and then the path in its `when`, with each path parameter
written `{field}` (`I GET /loans/{loan_id}`), and `get back <three-digit
status>` in its `then`. Acceptance tests are written by hand from the level-2
stories; the renderer writes none.

## 3 `composition.toml`

```toml
context = "loans"                     # required: the context package, snake_case
```

### `[aggregate]` — the aggregate's contract (required)

```toml
[aggregate]
name = "Loan"                         # required, PascalCase
identity = "loan_id"                  # required: a str field of both the spec and the reads

[aggregate.spec]                      # required: what it is built from, when submitted and when loaded
loan_id = "str"
borrower = "str"

[aggregate.reads]                     # required: what the application reads off it
loan_id = "str"
borrower = "str"
```

Only this contract is rendered in the domain: `<Name>Spec` with the spec's
fields, the aggregate constructed from it,
and one read per `[aggregate.reads]` entry. Everything else in the domain
(value objects, validation, how a read is computed) is the agent's.

The aggregate is saved by reading it back: a port record of the aggregate
holds the spec's fields, filled from the reads of the same name, so every spec
field needs a read of the same name.

### `[interfaces.http]` (required)

```toml
[interfaces.http]
serves = ["s-1-a-1", "s-1-b-1"]       # the level-2 stories the HTTP routes are
```

### `[client.operations.<operation>]` — the context's public interface (at least one)

```toml
[client.operations.lend_book]
kind = "write"                        # informational
request = ["borrower", "title"]
response = ["loan_id"]
steps = ["identity.issue_loan_id", "repository.save_loan", "orchestrator.start_arrange_loan"]
serves = ["s-1", "s-1-a-1"]           # exactly one of these must be in [interfaces.http] serves
```

Each operation is one route: the method, path, and status of the one served
level-2 story it names. Its request fields are read from the path (a
`{field}` in it) or else from the JSON body (as text, or an integer for
`int`); its response fields are answered as JSON.

**Steps**, in order:

- `identity.<operation>` / `repository.<operation>`: call that port
  operation (looked up by operation name across `[ports]`). If its request
  names the aggregate, the aggregate is built first from what the earlier
  steps hold (the request, the answers so far). If
  its response is the aggregate, the aggregate is rebuilt from it.
- `orchestrator.run_<operation>`: run the orchestrator operation and wait for
  its answer.
- `orchestrator.start_<operation>`: start it and answer at once; its answer is
  `Start<Operation>Response`, carrying the identity. Put a
  `repository.save_...` step before it to save before starting, so the
  aggregate is readable at once.

**Where each field comes from.** Every message a step sends (and the
operation's answer) is filled field by field from what the method holds, newest
first: the answers of the steps before it, then the aggregate's reads once it
is built, then the request. A field nothing holds is a problem.

### `[orchestrator.operations.<operation>]` — the workflow (exactly one)

```toml
[orchestrator.operations.arrange_loan]
request = ["loan_id", "borrower", "title"]   # must include the identity: it keys the workflow
response = ["loan_id"]
steps = ["actions.notice.send_notice", "actions.loan.record_loan", "signal.await_return_book"]
```

Steps, in order: `actions.<key>.<operation>` runs an action;
`signal.await_<signal>` waits on the signal's durable promise. Fields are
filled as for client steps.

### `[signals.<name>]` — a durable promise (optional)

```toml
[signals.return_book]
payload = ["loan_id"]                 # what the promise resolves with: the await's answer
resolved = false                      # required false: only the wait is rendered
```

The wait takes the identity. Resolving the promise is not rendered.

### `[actions.<key>]` — classes of actions, one port each

```toml
[actions.loan]
port = "LoanRepository"               # required: the one port this class calls

[actions.loan.operations.record_loan]
calls = "save_loan"                   # required: the one port operation it calls
request = ["loan_id", "borrower", "title"]
response = ["loan_id"]
builds = "Loan"                       # optional: build the aggregate from the request
```

The class is `<Key>Actions`. An action calls its port once.

### `[ports.<Port>]` — the contracts an implementation satisfies

```toml
[ports.NoticeSender]
operations.send_notice = { request = ["borrower", "title"], response = [] }

[ports.LoanRepository]
operations.save_loan = { request = ["loan"], response = [] }
operations.load_loan = { request = ["loan_id"], response = ["loan"] }

[ports.LoanIdentityRepository]
operations.issue_loan_id = { request = [], response = ["loan_id"] }
```

A port whose operations name the aggregate is a **store**: it has exactly one
save (request `[<aggregate>]`, response `[]`) and one load (request
`[<identity>]`, response `[<aggregate>]`), its name ends in `Repository`, and
its store is the same name ending in `Store`.

`serves = [...]` is allowed on any table and read by no one yet.

## 4 `implementations.toml`

```toml
app = "library"                           # required: the app, snake_case

[implementations.LoanRepository.memory]   # [implementations.<Port>.<key>]
body = "supported"

[implementations.LoanIdentityRepository.uuid]
body = "supported"

[implementations.NoticeSender.printed]
class = "PrintedNoticeSender"             # required with body = "agent"
body = "agent"

[engine.restate]                          # required, and the only engine
body = "supported"
ingress_variable = "RESTATE_INGRESS"      # required: the variable the app reads the ingress from
admin_variable = "RESTATE_ADMIN"          # required: read by the tests that register an endpoint
callback_host_variable = "RESTATE_CALLBACK_HOST"   # required: likewise

[environments.gate]                       # [environments.<name>], at least one
implementations = { NoticeSender = "printed", LoanRepository = "memory", LoanIdentityRepository = "uuid" }
engine = "restate"
hosts = ["http"]

[hosts.http]                              # required, and the only host
engine_path = "/restate"                  # required: where the Restate endpoint is mounted
listen_port_variable = "LIBRARY_PORT"     # required: the port it listens on when not given one

[variables]                               # informational: what each variable is
RESTATE_INGRESS = "..."
```

Every port needs an implementation in every environment, and the same one in
each (differing ones would need a selector variable, which is not rendered).
The implementation types:

- `memory`, `body = "supported"`: a store port only; an in-memory store,
  rendered in full.
- `uuid`, `body = "supported"`: a port with one operation that takes nothing
  and answers one field; issues version-4 UUIDs from a seed, rendered in full.
- any key with `body = "agent"` and a `class`: a stub gateway of that class,
  agent-owned (below).

## 5 `generator.toml`

```toml
[sample_values]
loan_id = ["loan-1", "loan-2"]           # two values per field
borrower = ["Ada", "Grace"]
```

Every field the generated tests need a value for must have one, listed here.

## What is rendered, and who owns it

Every rendered file says on its first line who owns it:

- `# pragma: tesser-generated; ...` — the renderer's. Change the composition
  and render again, never the file.
- `# pragma: tesser-agent-owned; ...` — rendered once as a stub, then the
  agent's: `<context>/domain/<aggregate>.py` with its `__init__.py` and
  `test_<aggregate>.py`, and each `body = "agent"` implementation
  (`<context>/adapters/gateways/<class>.py` and its test). A stub answers
  placeholders and never raises: a str read answers what the spec holds, a gateway
  `""`, `0`, or an empty list for each field it answers.

`.tesser-root` carries no marker: its lines are declarations only.

The rendered tree: `<context>/domain`, `client`, `application` (the
`<Aggregate>Service`, each `<Key>Actions`, `ports/`, `relays/` with their
snapshots, `client/` application clients, `orchestrators/`), `adapters`
(Restate `activities/`, `workflows/`, `dispatchers/`, the `handlers/http.py`
HTTP handler, `repositories/`, `gateways/`), `component/`; then `app/`,
`protocol/`, `srv/http/main.py` (the HTTP host serving the routes with the
Restate endpoint at `engine_path`), `pyproject.toml`, `requirements-dev.txt`,
`conftest.py`, and `.tesser-root`. Every module has its sibling test.

**Derived names** (never written in a spec): `<Aggregate>Service`,
`<Aggregate>Orchestrator` and its `<Aggregate>OrchestratorRelay`,
`<Aggregate>OrchestratorSignalRelay` and a `<SIGNAL>_PROMISE` constant,
`<Key>Actions` and its `<Key>ActionsRelay` and `<Key>ApplicationClient`,
`<Operation>Request` / `<Operation>Response` for every operation, the engine
containers (one per class of actions, named `<Key>Actions`, and the workflow,
named `<Aggregate>Orchestrator`), `Restate<Operation>` for each activity and the
workflow, `RestateHttp<Aggregate>OrchestratorRelay`, `Memory<Port>` /
`Memory<Store>`, `Uuid<Port>`, `<Context>Client`, and the app `<App>App`.

## Checklist for a new composition

1. `language.toml`: the terms and their code names.
2. `story.toml`: level-1 and level-2 stories; each level-2 route story names
   its method and path in `when` and `get back <status>` in `then`.
3. `composition.toml`: `context`; the aggregate's spec and reads (identity in
   both, every spec field readable); one client operation per level-2 story,
   its steps in order; exactly one orchestrator operation whose request holds
   the identity; its actions (one port each) and any signal; every port.
4. `implementations.toml`: `app`; an implementation for every port;
   `[engine.restate]` with its three variables; an environment; `[hosts.http]`.
5. `generator.toml`: two sample values for every field.
6. Render into a fresh directory and run the gate on it.
