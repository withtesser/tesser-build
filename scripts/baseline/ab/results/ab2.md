# A/B run 2: a restart must be survived, and the infra is given (Opus, medium)

What changed from run 1: story-drafting gained s-3 (a drafted job to be done is
still there, with the same stories, after the service restarts); `infra.toml`
(the engineer's decisions: Python 3.12, Restate, SQLite at `JTBD_DB_PATH`) is a
sixth spec given to red and green and stated in the bare prose; the renderer
hands green an agent-owned store to make durable; the shared check restarts the
service between two reads. N = 1, Opus, medium effort, one system prompt for
every agent. Red and arm B ran at the same time; green ran alone.

| | Arm A (red + green) | Arm B (bare) |
|---|---|---|
| Agent time | 136.6 s + 159.1 s = **295.7 s** | **334.9 s** |
| Tool calls | 10 + 18 = 28 | 42 |
| Shared check: submit, read, read after restart | pass, pass, pass | pass, pass, pass |
| Automated tests | 80 (gate) | none (checked by curl and shell) |
| Implementation coverage | 90.0% | 0% |
| Acceptance tests for the stories | s-1 and s-2 through the served host; s-3 has no route, so a store unit test only | none |
| Files / Python lines written by the agent | red: 3 specs + 2 tests; green: 6 files, 125 impl + 78 test lines | 9 files, 275 lines |
| Store | agent-owned `SqliteJtbdRepository` (stdlib `sqlite3`), red's choice from infra.toml | SQLite file, plus a Restate workflow |
| Durable wait at the checkpoint | no (red dropped the signal again) | yes (a Restate promise) |
| Unknown id | 500 | 404 |
| tessercheck | 0 findings, integrity ok | not applicable |

## Reading it

- **Run 1's persistence gap closed.** In run 1 red picked an in-memory store and
  arm A failed the restart check. With s-3 and `infra.toml`, red chose an
  agent-owned SQLite repository and green made it durable; arm A now passes.
- **Arm A is faster by about 12% on agent time and used a third fewer calls**,
  against a 9% gap in run 1 (254 s against 276 s). N = 1; do not read it as more
  than "not slower".
- **What arm A still lacks:** the durable checkpoint wait (no story names it), a
  404 for an unknown id, and an acceptance test for s-3 (the renderer allows one
  routed story per route).
- **What arm B still lacks:** any test at all, and its own shutdown workaround:
  the Restate SDK replaces the SIGTERM handler, so it puts one back in `main.py`.

## Caveats

N = 1 per arm; the story-drafting case is the one the generator was shaped
around; arm B also pays for creating and populating its own virtualenv.
Gate and setup time are not separated here.
