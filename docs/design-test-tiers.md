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
  from the test process — the component publishes its engine containers, the
  test registers them under fresh names, as the adapter tests already do — so
  the workflow's callbacks land in the process whose client reads the result.
  One process: nothing to share, so in-memory adapters are enough.

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
