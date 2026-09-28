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

## The runner's order

Container names are literals (TB085), so a context test and a served host
would claim the same names on the tree's engine. The runner keeps them apart
in time rather than renaming either:

1. every tier but the root runs first, with **no host served** — a context
   test registers the component's containers from its own process, and an
   adapter test registers its own objects under fresh names as before;
2. the runner then serves the hosts (and registers the engine host, forcing
   over whatever the context tier left);
3. the root tier runs last, against the served hosts.

A tree's verify arm is two pytest runs around the hosts:
`pytest --ignore=tests`, serve, `pytest tests`. A second engine server per
tree would also work, but it doubles the infrastructure to solve an ordering
problem. Renaming a built container after the fact (reaching into the SDK's
service tag) is refused: it is a test changing a production object's identity
through an undocumented attribute.

## Reaching a host from a root test

`tesser.testing` carries the two things every root test needs, so no tree
writes its own:

- `ts.Cli("srv.cli.main").run(*args)` runs a CLI host as a subprocess with the
  caller's import path and environment, and answers a `ts.CliAnswer`
  (`exit_code`, `stdout`, `stderr`, `lines()`).
- `ts.served("APP_URL")` reads the address the runner named for a served host,
  and refuses loudly when the runner did not set it.

`tesser.testing` is the one `tesser` namespace allowed `os` and `subprocess`
(TB062): it is imported only by tests, and running a host is what a root test
does.

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
- **The runner owns the hosts.** The verify arm serves long-running hosts and
  puts their addresses in the environment, as it already serves the Restate
  endpoint; a CLI host is a subprocess per command.
