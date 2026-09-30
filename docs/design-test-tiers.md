# Test tiers: the root tier plays the user, the context tier plays a caller

Ruled 2026-09-28. Supersedes the root-tier row that let a root test reach a
context "through its component and client".

## The rule

A test's placement fixes who it plays, and who it plays fixes what it may
import (TB070).

- **Root `tests/` — end to end, plays the user.** A story's acceptance test
  lives here. It reaches the app only through a **running host**, speaking the
  app's public wire format: a CLI host run as a subprocess, an HTTP host at an
  address the runner puts in the environment. It imports `protocol` (to build
  requests and read answers), its own `tests` support modules, and — in a
  library tree with no host — the tree's exported kernel. Never `app`, `srv`, a
  context, or a kernel. Hosts are processes; the root tier never builds a host
  in-process, so the rule is one import row with no exceptions.
- **Context `<ctx>/tests/` — the component's contract, plays a caller.** It
  builds the component in the test process and drives it through its client
  and handlers. Neighbouring contexts are hand-written fakes at the port; a
  third party is a fake at its gateway's port. A durable workflow is served
  from the test process — the component publishes its engine containers, and
  the test serves and registers them **under the component's own names** — so
  the workflow's callbacks land in the process whose client reads the result.
  One process: nothing to share, so in-memory adapters are enough.

## The tests own their infrastructure

Ruled 2026-09-30, superseding "the runner's order". A run of plain `pytest`
from the tree's root runs every tier, in any order, with nothing served
beforehand and nothing read from the environment. The tree's root
`conftest.py` owns what the tests need, as session fixtures a test asks for
by name:

- `engine_url`, `engine_admin_url`, `engine_callback_host` — a **private
  Restate engine** for every tier but the root, started on first use
  (`restate.harness`, a container per run) and removed at the end. A context
  test serves the component's containers from its own process and registers
  them **under the component's own names**, at `engine_callback_host`; an
  adapter test registers its own objects under fresh names as before.
- `free_port` — a port the OS just handed out, for a test that serves an
  endpoint.
- `host` — for the root tier: a **second private engine**, and the tree's
  HTTP host served on a free port as a subprocess and registered with that
  engine. The root tier's host is a process, as the rule above says; the
  fixture is what starts it.

**Two engines, because the names clash.** Container names are literals
(TB085), and Restate routes a service's new invocations to its latest
registration. Measured on one engine: once a context test registered the
component's names, the served host's new runs went to the test process, and
the host could not read them back; when the test deleted its deployment,
routing returned to the host. One engine per tier keeps the two apart without
renaming either, and without ordering the tiers in time. Renaming a built
container after the fact (reaching into the SDK's service tag) stays refused:
it is a test changing a production object's identity through an undocumented
attribute.

**Nothing leaks when the run dies.** Each engine and the served host carry a
watchdog: a child process that blocks reading a pipe from pytest and, when the
pipe closes without being told to stand down (pytest killed), removes the
container or kills the host's process group. testcontainers' own reaper is
not relied on — on Docker Desktop its client connects before the reaper
listens and the reaper never learns what to remove.

**An infrastructure fixture is synchronous.** It yields plain values (URLs,
ports), so a session-scoped resource never belongs to one test's event loop
(`asyncio_default_fixture_loop_scope = "function"`); only per-test clients are
async.

The cost is Docker at test time and a container start per engine (about a
second once the image is pulled). A tree without an engine has none of these
fixtures.

## Reaching a host from a root test

A CLI host is run directly: `subprocess.run([sys.executable, "-m",
"srv.cli.main", *args], capture_output=True, text=True, check=False,
env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)})`. The test's own
`sys.path` becomes the child's `PYTHONPATH`, so the host imports what the test
could, and the answer is the `CompletedProcess` (`returncode`, `stdout`,
`stderr`); there is no wrapper to learn.

An HTTP host's address is the `host` fixture: a root test takes `host: str` as
a parameter and never reads the environment. Without options the fixture
serves the tree's own host, as above. `pytest --host <url>` points the root
tier at a host that is already running — a deployed one a smoke run checks —
and then the fixture serves nothing. The address is the caller's
configuration, as a base URL is for any client of an HTTP service, so it is
one option named the same in every tree, and `tesser.testing` carries nothing
for it.

Root tests share a served host for the whole run, so each uses its own data —
a fresh identity or a random value — and asserts only on what it created.

## Why

The old root row let a test build the whole app in its own process and call
the client. Two things followed, both observed in the story-drafting
baselines (`scripts/baseline/results/`):

1. **The test reached around the app it claimed to accept.** The served host
   (the Restate endpoint) wrote state; the test's *own copy* of the app read
   it back. The served app's read path was never exercised — a host with
   broken read wiring passed.
2. **Test topology became production design.** Two copies of the app in two
   processes need a channel. In a tree with only Restate, two independent
   agents both invented a file-backed JSON store whose only reason to exist
   was the test. Where Postgres is a real dependency (`examples/voice`) the
   same shape looks legitimate — another replica reading the shared database —
   which is why the examples taught it.

Host-only removes the incentive at both tiers: at the root the read goes
through the host, so the host decides where state lives; at the context tier
there is one process, so there is nothing to bridge. Whether a store the app
has is *justified* stays a review question; the rule removes the reason to
add one for a test.

## Consequences

- **Every user-facing story needs a host that exposes it** — the write and
  the read the acceptance test observes. A story with nothing observable
  through a host has no acceptance test: either it is not user-facing, or its
  read is missing.
- **The root tier is slow and small**: one test per story. Behaviour
  scenarios belong to the context tier.
- **The tests own the hosts.** The root `conftest.py` serves a long-running
  host for the session and a CLI host is a subprocess per command; a verify
  arm is plain `pytest`, and `tests` sits in `testpaths` like every tier.
