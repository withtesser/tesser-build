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

**The output directory** may already hold files, and rendering again is how a
tree follows its composition:

- a file the renderer does not write (a `README.md`, a `specs/` directory
  holding the composition itself) is left where it is;
- a file marked generated (below) is overwritten;
- an agent-owned file that already exists is kept as it is;
- a file where a generated one goes that is not marked generated, and differs,
  is a problem.

If anything is a problem, nothing is written. Every rendered path stays inside
the output directory: the renderer refuses a path that resolves outside it,
symlinks included, and two pieces rendering one path.

**Checking a tree against its composition:**

```sh
PYTHONPATH=.:../tesser-py python3 -m srv.cli.render --check <composition-dir> <tree>
```

renders in memory, writes nothing, and exits 1 naming each generator-owned
file that differs from what the composition renders, is missing, or has lost
its generated mark (agent-owned files are not checked); otherwise it exits 0.
A tree in this repo that the renderer wrote carries a `.tesser-rendered` file
whose first line is its composition directory, relative to the repo root; its
`scripts/verify` arm runs the check first.

**Names.** Every name that reaches a path or an identifier is checked: the
context, app, fields, action keys, and enum members and outcomes are
snake_case (`loan_id`); operations, commands, and signals are snake_case of at
least two words (`lend_book`); the aggregate, ports, shapes, messages, enums,
and implementation classes are PascalCase (`LoanRepository`); variables are
UPPER_CASE; `engine_path` is a lowercase URL path. None may be a Python
keyword, and the context may not be one of the rendered tree's own package
names (`adapters`, `app`, `application`, `client`, `component`, `config`,
`conftest`, `domain`, `identity`, `pgdatabase`, `protocol`, `spec`, `srv`,
`tests`).

Every directory in `generator/compositions/` is gated: `scripts/verify
generator` renders it and runs the rendered tree's tessercheck (zero findings),
`mypy --strict`, and every test tier but the root. `library/` is the small
worked example.

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
- an enum's name (declared in `[enums]`); it crosses every message as its string value
- `"<Shape>[]"`: a list of a shape or message (declared in `[shapes]` or
  `[messages]`). A shape's own fields are `str`, `int`, or enums, never lists.
  A shape is never carried alone, only as a list.
- the aggregate's snake_case name (`loan` for `Loan`), only in a port
  operation: the whole aggregate as its port record.

**Where a field's type comes from.** A field is named by its bare name in
every list (`request = ["loan_id", "borrower"]`). Its type is looked up, in
order: the aggregate's `[aggregate.spec]`,
each command's `takes`, a port annotation (`"story_texts: StoryText[]"` in a
port operation's list, which types that field of that operation only),
then `[aggregate.reads]`.
A client operation's `response` looks in the reads first, so a read that
differs from the spec field of the same name (`stories`: `StorySpec[]` in the
spec, `StoryView[]` in the reads) answers the read's type.
Every field named anywhere must get a type this way.

## 1 `language.toml`

Read only to check it is TOML; everything in it is for people. Its shape (as in
`library/language.toml`): `context = "<context>"`, then `[[terms]]` tables with
`term`, `means`, `code_names = [...]`, and optionally `short`, `status`, `not`,
`note`, and a `[conventions]` table. Write it first: every other file uses its
code names.

## 2 `story.toml`

A tree of JTBDs and stories. The renderer reads two things from it: story ids,
and each HTTP-served level-2 story's `route`, `status`, `when`, and `then`: the
route and status are those of the client operation that serves the story, and
its `when` and `then` must state them.

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
when = "I POST them as JSON to /loans"          # says the method and the path
then = "I get back 201 with its loan_id"        # says the status
route = "POST /loans"                           # the method, a space, and the path
status = 201                                    # the 2xx it answers with
reached_by = "..."                              # optional, for the acceptance test's given
```

A route is observable, so it belongs to the level-2 story: each level-2 story
an HTTP route serves carries its `route` — the method (`GET`, `POST`, `PUT`,
`PATCH`, `DELETE`), a space, and a path of lowercase segments and `{field}`
parameters — and its `status`, the 2xx it answers with. The `given`, `when`,
and `then` stay prose, and the prose must state the route word for word: the
method and the path are words of the `when` (`I GET /loans/{loan_id}`) and the
status is a word of the `then` (`I get back 200 ...`). A level-2 story with a
route that no client operation serves is a problem. Acceptance tests are
written by hand from the level-2 stories; the renderer writes none.

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

[aggregate.commands.record_stories]   # optional, any number
takes = { story_texts = "StoryText[]" }                   # the command's input fields
outcomes = ["recorded", "already_recorded", "none_given"] # required, at least one
```

Only this contract is rendered in the domain: `<Name>Spec` with the spec's
fields, the aggregate constructed from it,
one method per command taking `<Command>Spec` (its `takes`) and answering
`<Command>Outcome`,
and one read per `[aggregate.reads]` entry. Everything else in the domain
(value objects, validation, how a read is computed) is the agent's.

The aggregate is saved by reading it back: a port record of the aggregate
holds the spec's fields, filled from the reads of the same name, so every spec
field needs a read of the same name.
A list read's shape must hold every field it reads from the spec shape's.

### `[shapes.<Name>]`, `[messages.<Name>]`, `[enums]` (optional)

```toml
[shapes.StorySpec]      # a shape: fields of str, int, or enums
given = "str"
state = "StoryState"

[messages.StoryText]    # the same form; a message crosses ports and relays
given = "str"

[enums]
StoryState = ["drafted", "accepted", "rejected"]
```

A shape named `...Spec` is the domain spec of that name; any other shape's
domain spec is `<Name>Spec`.

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

Each operation is one route, and it is the route of the level-2 story it
serves: of the stories in its `serves`, exactly one is a level-2 story with a
`route`, and that story is in `[interfaces.http] serves`. Its request fields
are read from the path (a `{field}` in it) or else from the JSON body (as
text, or an integer for `int`); its response fields are answered as JSON. Two operations may call the same port
operation; each gets its own mapper.

**Steps**, in order:

- `identity.<operation>` / `repository.<operation>`: call that port
  operation (looked up by operation name across `[ports]`). If its request
  names the aggregate, the aggregate is built first from what the earlier
  steps hold (the request, the answers so far), with any list field empty. If
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
is built, then the request. An aggregate rebuilt from a load takes the fields
the earlier steps hold (the request, say) over the loaded ones, so a load then a
save writes what the operation was given. A field nothing holds is a problem, except a list
field of the aggregate's spec, which starts empty.

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
commands = ["record_stories"]         # optional, needs builds: give it this one command...
calls_on = ["recorded"]               # ...required with commands: the outcomes that make the call
```

The class is `<Key>Actions`, and it may carry several operations; every one
must be a step of the orchestrator operation. An action calls its port once.
With `commands`, it matches the command's outcome: the outcomes in `calls_on`
(each one of the command's `outcomes`) make the call, the others answer
without it.

### `[ports.<Port>]` — the contracts an implementation satisfies

```toml
[ports.NoticeSender]
operations.send_notice = { request = ["borrower", "title"], response = [] }

[ports.StoryDrafter]
operations.draft_stories = { request = ["role"], response = ["story_texts: StoryText[]"] }

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

Every environment names an implementation for every port, and the same one as
every other environment (differing ones would need a selector variable, which
is not rendered).
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
story_texts = [                          # a list field: two lists of tables
  [{ given = "...", when = "...", then = "..." }],
  [{ given = "...", when = "...", then = "..." }],
]
```

Every field the generated tests need a value for must have one, listed here,
or inside a listed list of tables (a shape's field found in another sample),
or an enum (its members are used). A list field with no sample is built from
its shape's fields.

## What is rendered, and who owns it

Every rendered file says on its first line who owns it:

- `# pragma: tesser-generated; ...` — the renderer's. Change the composition
  and render again, never the file (`--check` catches an edit).
- `# pragma: tesser-agent-owned; ...` — rendered once as a stub, then the
  agent's: `<context>/domain/<aggregate>.py` with its `__init__.py` and
  `test_<aggregate>.py`, and each `body = "agent"` implementation
  (`<context>/adapters/gateways/<class>.py` and its test). A stub answers
  placeholders and never raises: a str read answers what the spec holds, a
  command its last outcome, an enum read its first value, a gateway
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
2. `story.toml`: level-1 and level-2 stories; each level-2 story an HTTP
   route serves carries its `route` and `status`, and its `when` and `then`
   say them word for word.
3. `composition.toml`: `context`; the aggregate's spec and reads (identity in
   both, every spec field readable); one client operation per level-2 story,
   serving it and its steps in order; exactly one orchestrator operation whose request holds
   the identity; its actions (one port each) and any signal; every port.
4. `implementations.toml`: `app`; an implementation for every port;
   `[engine.restate]` with its three variables; an environment; `[hosts.http]`.
5. `generator.toml`: two sample values for every field.
6. Render into a fresh directory and run the gate on it.
