# Compositions: the six spec formats `srv.cli.render` reads

A composition is a directory holding six TOML files. `srv.cli.render` reads them
and writes a complete tesser app tree:

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.render <composition-dir> <out-dir> [--print <rendered-path>]...
```

It prints the path of every file it wrote, one per line (then `kept <path>` for
each agent-owned file it left alone), and exits 0; or it prints every problem
on stderr as `render: <problem>`, exits 1, and writes nothing. Each `--print`
(repeatable) names a rendered path, relative to the output directory; after
the list, each one follows as a `--- <path>` line and then the file verbatim,
as the render leaves it (so a kept agent-owned file prints as it stands). A
`--print` path the composition does not render is a problem.

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
Every render writes `.tesser-rendered` (generator-owned, and like
`.tesser-root` it carries no marker): its one line is the composition
directory, relative to the root of the git repo the output directory is in
when the composition is inside that repo, else absolute. A tree's
`scripts/verify` arm runs the check first when the file is there, so a
rendered tree is checked against its composition by default.

**Names.** Every name that reaches a path or an identifier is checked: the
context, app, storages, fields, action keys, and enum members and outcomes are
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
`mypy --strict`, and a plain `pytest` from its root, which starts the engines
and the host the tests take (Docker required); it passes when every failure is
a root-test skeleton red at its placeholder. `library/` is the small
worked example.

## Which file answers which question

| File | Question | Written by |
|---|---|---|
| `language.toml` | What do our words mean? | the product owner, with the agent |
| `story.toml` | What must a user be able to observe? | the product owner |
| `infra.toml` | What does this app run on, and what must an operator provide? | the engineer, up front (never red) |
| `composition.toml` | Which pieces exist and how do they connect? The contracts only. | the agent, reviewed |
| `implementations.toml` | Which implementation satisfies each port, in which environment? | red, reviewed |
| `generator.toml` | Sample values for the generated tests, and nothing a reviewer cares about. | anyone |

Each fact lives in one file. `infra.toml` holds the technology decisions (the
app, the runtime, the engine, the host, the storages, the variables) and never
a contract or a port; `composition.toml` never says what implements a
contract; `implementations.toml` never declares a contract, and holds only the
port-level mapping (`[implementations]` and `[environments]`): an
`implementations.toml` that still carries `app`, `[engine]`, `[hosts]`, or
`[variables]` is a problem saying each moved to `infra.toml`. Names in
`composition.toml` are words of the domain (`language.toml`'s terms) or words
the conventions derive (below); the renderer checks one thing against the
language, the key of a class of actions (below).

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

Read for one thing only: the names a class of actions may take. Everything else
in it is for people, and it holds meanings only (no rules, no design, no tooling,
no code names). Its shape (as in `story-drafting/language.toml`):
`context = "<context>"`, then `[[terms]]` tables with `term` and `means`, and
optionally `short`, `status`, `not` (the words not to use), and `note`. Write it
first: every other file speaks its words. A `[actions.<key>]` class of actions is
named for the domain term it acts on: the key must be the snake_case of a term's
name (`story`, `job_to_be_done`) or of its `short` form (`jtbd`), or an entry of
an optional `code_names = [...]` on a term (older compositions, such as
`library`, still list them).

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

[[jtbds.stories.jtbds.stories]]
id = "s-1-b-1"
given = "the loan_id of a lent book"
when = "I GET /loans/{loan_id}"
then = "I get back 200 with its borrower and title"
route = "GET /loans/{loan_id}"
status = 200
```

A route is observable, so it belongs to the level-2 story: each level-2 story
an HTTP route serves carries its `route` — the method (`GET`, `POST`, `PUT`,
`PATCH`, `DELETE`), a space, and a path of lowercase segments and `{field}`
parameters — and its `status`, the 2xx it answers with. The `given`, `when`,
and `then` stay prose, and the prose must state the route word for word: the
method and the path are words of the `when` (`I GET /loans/{loan_id}`) and the
status is a word of the `then` (`I get back 200 ...`). A level-2 story with a
route that no client operation serves is a problem.

A level-2 story's `given` is prose: it says in words how the story is reached
(`I have created a loan with POST /loans`). The renderer never reads it for
calls; the root test's author does. A story with a `reached_by` key is a
problem, because the key is no longer part of the format.

**Root test skeletons.** For each level-2 story with a route, the renderer
writes an agent-owned `tests/test_<words>.py`, named for its route: the method as a word (`GET` reading, `POST` submitting, `PUT`
replacing, `PATCH` updating, `DELETE` deleting), then each segment of the path
in order, a literal segment as it is and a `{field}` segment as `by_<field>`,
so `POST /jtbds` is `tests/test_submitting_jtbds.py` and
`GET /jtbds/{jtbd_id}` is `tests/test_reading_jtbds_by_jtbd_id.py` (so `GET
/jtbds` and `GET /jtbds/{jtbd_id}` are two files). It takes the served host's
address as the `host` fixture (`def test_<story>(self, host: str)`), calls the
story's route on it, and asserts its `status`, and holds two placeholders. The first is the given: an assertion whose
message is the story's `given`, verbatim, with a `<field>: <type> | None = None`
line above it for each `{field}` the route's path carries; the author writes how
the host reaches the given (which calls, any waiting) and binds those values in
its place. A route with no path value has nothing to bind, and the placeholder
is `assert False, ...`. The second is the then: an assertion whose message is
the story's `then`, verbatim. So a freshly rendered tree is red at the first
unwritten placeholder, then at the then, and rendering again keeps the edited
test.

Beside the skeletons the renderer writes an empty generated
`tests/__init__.py`, and the rendered root `conftest.py` holds the session
`host` fixture the skeletons take: it starts a private Restate engine, serves
`srv.http.main` with the engine's URL, a fresh temporary path for every storage
`location_variable`, and a free port in the `listen_port_variable`, registers
the host's `engine_path` with the engine, and yields the host's address. A
runner that already serves a host passes its address instead:
`pytest tests --host http://127.0.0.1:<port>` (`docs/design-test-tiers.md`,
"The tests own their infrastructure"). The address is an argument, not a
variable, so `infra.toml` declares none for it.

## 3 `infra.toml`

What the app runs on and what an operator must provide: the engineer's
technology decisions, made up front, before any contract, and never written by
red. A composition without it is a problem.

```toml
app = "story_drafting"                    # required: the app, snake_case

[runtime]                                 # informational: read by no one yet
language = "python"
version = "3.12"

[engine.restate]                          # required, and the only engine
body = "supported"                        # informational
engine_path = "/restate"                  # required: where the Restate endpoint is mounted
engine_url_variable = "RESTATE_URL"       # required: the variable the app reads the engine's URL from

[hosts.http]                              # required, and the only host
serves = "interfaces.http"                # informational: the composition's interface it serves
mounts_engine_endpoint = true             # informational: the engine endpoint is served in the same process
listen_port_variable = "STORY_DRAFTING_PORT"   # required: the port it listens on when not given one

[storage.sqlite]                          # [storage.<name>]: where stored things live
location_variable = "JTBD_DB_PATH"        # the variable that names its location (a SQLite file path)

[variables]                               # informational: what each variable is
JTBD_DB_PATH = "the path of the SQLite database file"
```

The engine names one variable, the one the app reads its URL from. The tests
never read the environment: they take the engine's URL, its admin URL and the
host name it reaches a served endpoint at as fixtures of the rendered root
`conftest.py`, so an `admin_variable` or `callback_host_variable` is a problem.
The host's variables stay, because the `host` fixture passes them to the host
it serves.

A storage is named by its key (snake_case). `[storage.memory]` needs no
`location_variable`, since it lives in the process; every other storage names
one, or it is a problem. A store port in `implementations.toml` is implemented
by a key that names a declared storage (below); a declared storage no port
uses is allowed. When a store port's storage has a `location_variable`, the app
reads that variable when it loads (refusing with `missing_env` when it is
unset, as it does the engine's URL), the component config carries it as
`<storage>_location`, and the component builds the store with
`location=config.<storage>_location`.

## 4 `composition.toml`

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
outcomes = ["recorded"]                                    # required, at least one; the first is the success outcome
```

Only this contract is rendered in the domain: `<Name>Spec` with the spec's
fields, the aggregate constructed from it,
one method per command taking `<Command>Spec` (its `takes`) and answering
`<Command>Outcome`
(a command with `takes = {}` gets a `<Command>Spec` whose constructor is a
single `pass`),
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
StoryState = ["drafted", "accepted"]
```

A shape named `...Spec` is the domain spec of that name; any other shape's
domain spec is `<Name>Spec`.

### Every listed piece is named by a story

The composition holds only what the current stories require. A piece a story
reader can see has to have a story behind it, or it is scope creep, so the
renderer checks the pieces below against `story.toml` and refuses (writes
nothing) when one is untraced:

- every value of every enum in `[enums]`;
- every field in each `[client.operations.*]` `request` and `response`;
- every field in `[aggregate.reads]`;
- every field in each `[signals.*]` `payload`;
- every outcome of each `[aggregate.commands.*]` `outcomes` except the
  success outcome, which is the first one listed (the renderer has no other
  notion of a normal-case outcome: `calls_on` may name several). A command
  may list a single outcome; its action then matches one case.

A piece is named when its name appears as a whole token in the `given`,
`when`, or `then` of at least one story at any level (a JTBD's `as`, `i_want`,
and `so_that`, the story's `route`, and `[scope] out` do not count; that list
is prose about non-goals). Case does not matter, and the name's underscores
may be written as spaces (`awaiting_story_acceptance` is named by "awaiting
story acceptance"); `loan` is not named by `loan_id`. Ports, port, action,
and relay fields, `[shapes]`, `[messages]`, and `[aggregate.spec]` fields are
not checked. Every untraced piece is one problem, all reported together:

```
render: enum JtbdStatus value stories_decided is named by no story: write it in a story's given, when, or then, or remove it from the composition
```

The fix is to write the piece in a story, or to remove it from the composition.

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
are read from the path (a `{field}` in it, as text, or an integer for `int`;
a path carries no other type) or else from the JSON body (as text, or an
integer for `int`); its response fields are answered as JSON. No two
operations have the same method and path, since HTTP would reach only one.
A path names each `{field}` once, since a route binds a parameter once: a
repeated one (`/loans/{loan_id}/{loan_id}`) is a problem. A path parameter for
an `int` field answers 400 unless it is an optionally negative run of at most
18 ASCII digits (`--2`, `+2`, `1_0`, and the empty string are all 400).
Two operations may call the same port operation; each gets its own mapper.

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
builds = "Loan"                       # optional: build the aggregate (its [aggregate] name) from the request
commands = ["record_stories"]         # optional, needs builds: give it this one command...
calls_on = ["recorded"]               # ...required with commands: the outcomes that make the call
```

The class is `<Key>Actions`, and it is named for the domain term it acts on,
never for its port: `<Key>` in PascalCase is exactly the PascalCase of a
term's name or short form in the language (`story` → `Story`, `jtbd` →
`Jtbd`, so `StoryActions`), or an entry of a term's optional `code_names`
(`loan` → `Loan` in `library`). A key that is none of those is a problem, even
when a term contains it: `drafter` on `StoryDrafter` is refused, since
`Drafter` is no term; the class is `story`. It may carry several operations; every one must be a step of the
orchestrator operation. An action calls its port once.
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

A port operation's name is declared by one port only: its
`<Operation>Request` and `<Operation>Response` are exported from one `ports`
package, so two ports declaring one name is a problem.

A port whose operations name the aggregate is a **store**: it has exactly one
save (request `[<aggregate>]`, response `[]`) and one load (request
`[<identity>]`, response `[<aggregate>]`), its name ends in `Repository`, and
its store is the same name ending in `Store`.

`serves = [...]` is allowed on any table and read by no one yet.

## 5 `implementations.toml`

Red's port-level mapping, and nothing else: which implementation satisfies each
port, and which is used in each environment. The engine, the hosts, the
storages, and the variables are `infra.toml`'s.

```toml
[implementations.LoanRepository.memory]   # [implementations.<Port>.<key>]; a store's key is a declared storage
body = "supported"

[implementations.LoanIdentityRepository.uuid]
body = "supported"

[implementations.NoticeSender.printed]
class = "PrintedNoticeSender"             # required with body = "agent"
body = "agent"

[environments.gate]                       # [environments.<name>], at least one
implementations = { NoticeSender = "printed", LoanRepository = "memory", LoanIdentityRepository = "uuid" }
engine = "restate"                        # the engine infra.toml declares
hosts = ["http"]                          # the host infra.toml declares
```

Every environment names an implementation for every port, and the same one as
every other environment (differing ones would need a selector variable, which
is not rendered). A store port (one that carries the aggregate) is implemented
by a key that is the name of a storage `infra.toml` declares: `memory` for
`[storage.memory]`, `sqlite` for `[storage.sqlite]`; a store implemented by a
key with no `[storage.<key>]` is a problem naming both.
The implementation types:

- `memory`, `body = "supported"`: a store port only, on `[storage.memory]`;
  an in-memory store, rendered in full.
- `uuid`, `body = "supported"`: a port with one operation that takes nothing
  and answers one field; issues version-4 UUIDs from a seed, rendered in full.
- any key with `body = "agent"` and a `class` on a gateway port: a stub gateway
  of that class, agent-owned (below).
- any key with `body = "agent"` and a `class` on a store port (one that carries
  the aggregate): a stub store of that class, agent-owned, in
  `<context>/adapters/repositories/<class>.py` with its sibling test. The class
  is the store (it satisfies the `<Name>Store` the actions and service take and
  has `transaction()`); its repository is `<class>Transaction`. The stub starts
  as a working in-memory store, equal to `memory`, so the tree passes every gate
  before the agent replaces the body with a durable one (a file, SQLite); no
  sample beyond the aggregate's is needed. On a storage with a
  `location_variable`, its `__init__` takes `location: str`, which the stub
  ignores until the agent writes the durable body, and its sibling test builds
  it on a temporary path. The port's kind decides gateway or store, not a key.

```toml
[implementations.JtbdRepository.sqlite]   # the storage infra.toml declares
class = "SqliteJtbdRepository"
body = "agent"
```

## 6 `generator.toml`

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
its shape's fields. A field listed with no values (`borrower = []`) is a
problem, since there is nothing to pick from.

## What is rendered, and who owns it

Every rendered file says on its first line who owns it:

- `# pragma: tesser-generated; ...` — the renderer's. Change the composition
  and render again, never the file (`--check` catches an edit).
- `# pragma: tesser-agent-owned; ...` — rendered once as a stub, then the
  agent's: `<context>/domain/<aggregate>.py` with its `__init__.py` and
  `test_<aggregate>.py`, each `body = "agent"` implementation
  (`<context>/adapters/gateways/<class>.py` and its test, or for a store port
  `<context>/adapters/repositories/<class>.py` and its test), and the root
  test skeletons in `tests/` (above). A stub answers
  placeholders and never raises: a str read answers what the spec holds, a
  command its first outcome (the success outcome), an enum read its first value, a gateway
  `""`, `0`, or an empty list for each field it answers.

`.tesser-root` carries no marker: its lines are declarations only.

The rendered tree: `<context>/domain`, `client`, `application` (the
`<Aggregate>Service`, each `<Key>Actions`, `ports/`, `relays/` with their
snapshots, `client/` application clients, `orchestrators/`), `adapters`
(Restate `activities/`, `workflows/`, `dispatchers/`, the `handlers/http.py`
HTTP handler, `repositories/`, `gateways/`), `component/`; then `app/`,
`protocol/`, `srv/http/main.py` (the HTTP host serving the routes with the
Restate endpoint at `engine_path`), `tests/` (the root tier's skeletons, its
generated `conftest.py` and `__init__.py`),
`pyproject.toml`, `requirements-dev.txt`, `conftest.py`, and `.tesser-root`.
Every module has its sibling test.

A gate that serves `srv/http/main.py` for the root tier stops it with SIGINT
and kills it if it has not exited two seconds later: a Restate endpoint
holding a suspended invocation otherwise keeps the host alive until Restate's
inactivity timeout, about a minute.

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

1. `language.toml`: the terms and their meanings, including every term a class
   of actions acts on (its name or short form is the class's key).
2. `story.toml`: level-1 and level-2 stories, which between them name every
   enum value, client field, read, signal payload field, and non-success
   command outcome the composition lists; each level-2 story an HTTP
   route serves carries its `route` and `status`, and its `when` and `then`
   say them word for word; a story whose given needs calls first says in its
   `given`, in words, how it is reached.
3. `infra.toml`: `app`; `[runtime]`; `[engine.restate]` with its
   `engine_path` and three variables; `[hosts.http]` with its listen port
   variable; a `[storage.<name>]` for each storage (every one but `memory`
   with its `location_variable`); `[variables]`.
4. `composition.toml`: `context`; the aggregate's spec and reads (identity in
   both, every spec field readable); one client operation per level-2 story,
   serving it and its steps in order; exactly one orchestrator operation whose request holds
   the identity; its actions (one port each, each named for the term it acts
   on, never for its port) and any signal; every port.
5. `implementations.toml`: an implementation for every port, a store's named
   for a storage `infra.toml` declares; an environment.
6. `generator.toml`: two sample values for every field.
7. Render into a fresh directory and run the gate on it, with every storage
   `location_variable` set; then write each root test's then where its
   skeleton's placeholder stands.
