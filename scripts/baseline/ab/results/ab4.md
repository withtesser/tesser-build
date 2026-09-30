# A/B run 4: the tests own their engines and host (Opus and Sonnet, medium, in parallel)

What changed from run 3:

- **The tests own their infrastructure (#33, #34).** Rendered trees' tests start their own Restate engines
  and serve their own host, and trials run main's `run_story_drafting` gate
  (render check, tessercheck, mypy, one plain pytest) on scaffold
  `story-drafting-scaffold-s9`.
- **`infra.toml` names no admin or callback variable any more.**
- **The round was run by `scripts/baseline/ab/round`, in parallel.** The first wave (both reds and both bare agents) ran together; each green
  started when its red was recorded.

N = 1 per cell, medium effort, one agent definition. The table is
`ab4-table.md` (generated); the per-sample metrics are `ab4-metrics.json`.

| | Opus A (red + green) | Opus B (bare) | Sonnet A (red + green) | Sonnet B (bare) |
|---|---|---|---|---|
| Agent time | 144.3 + 159.6 = **303.9 s** | **648.4 s** | 137.7 + 104.7 = **242.4 s** | **59.0 s** |
| Model's own time | 236.7 s | 302.0 s | 145.8 s | 33.9 s |
| Checking (gate, tests, analyzer) | 56.1 s | 8.0 s | 65.5 s | 0 s |
| Setup (venv, installs) | 0 s | 12.3 s | 0 s | 21.9 s |
| Probing by hand (running the service, curl) | 0 s | 314.0 s | 0 s | 1.1 s |
| Tool calls | 6 + 12 = 18 | 38 | 10 + 11 = 21 | 6 |
| Shared check: submit, read, read after restart | pass, pass, pass | pass, pass, pass | pass, pass, pass | pass, pass, pass |
| Automated tests | 80 (gate), 89.9% impl coverage | 3 (incl. a restart acceptance test) | 73 (gate), 89.5% impl coverage | none |
| Written by green / bare | 6 files, 118 impl + 84 test lines | 10 files, 456 Python lines | 5 files, 74 impl + 24 test lines | 3 files, 141 Python lines |
| Unknown id / missing field | 500 / 400 | 404 / 400 | 500 / 400 | 404 / 422 |
| Durable wait at the checkpoint | no | **yes** (a promise nothing resolves) | no | no |
| Most other agents running at once | 3 | 5 | 3 | 3 |

## Reading it

- **Every cell passed the shared check**, and both greens passed their gate
  with 0 findings and a clean integrity audit.
- **Opus B was the slowest arm this time: 648 s.** 314 s of it went on
  running its own service by hand. The Restate SDK's SIGTERM handler does not stop the process, so the
  agent put its own handler back and force-exits after a second, with a private asyncio attribute
  it notes may break. In run 3 the same problem cost Opus B far less. So this is one agent's path through a known trap, not a trend.
- **Sonnet B was fastest again: 59 s, six calls, no tests.** Its own
  restart check was muddied by its old process holding the port. The check's
  reap killed that leftover server (it was still listening) before the shared check
  ran.
- **Arm A's times are close to run 3's**, with containers now started by the
  tests. Opus A took 304 s against 360 s, and Sonnet A 242 s against 196 s.
  The gate's checking time was 56–66 s against 56–63 s. Starting the private
  engines did not visibly cost time at this N. The runs overlapped with up to
  five others, so the times aren't strictly comparable with run 3's serial
  runs.
- **The two reds converged on one design this time.** Both used a drafter
  gateway (`FixedStoryDrafter`, `TemplatedStoryDrafter`), a `record_stories`
  command, and an agent-owned SQLite store. In run 3 they differed.
- **Opus B built the durable checkpoint wait without being told to.** In run
  3, with the same prompt, it didn't. So round 2's "the bare agents built it because we told them"
  is only part of the story: unprompted, Opus built it in one of its two runs.
  No story asks for it, and nothing resolves the promise.
- **Arm A still answers 500 for an unknown id and 400 for a missing field.**
  Both bare agents answer 404. No story names either case.

## Harness defects this run found

1. **The time split counted running the service as setup.** `\bvenv\b`
   matched `.venv/bin/python main.py`, and setup is matched before probing. Fixed: setup is now
   creating a virtualenv (`-m venv`, `virtualenv`), installs, and containers.
   Runs 3 and 4 are re-split from their transcripts; `ab3.md` and
   `ab3-table.md` carry the corrected numbers. Run 2 was affected too: its
   "91 s of setup" was 46 s of setup and 74 s of running its service. So the
   earlier reading that a cold pip cache explained run 2's arm B time
   overstated it.
2. **The prompts' gate command did not activate the venv.** The prompts say
   to prefix commands with `source {venv}/bin/activate &&`, but the printed
   gate command left it out. Before #34 that did not matter. Now the tests
   import `testcontainers`, which only the venv has. Sonnet red spent one gate
   run on it. Fixed in `red-specs.md` and `green-on-red.md` after this run, so
   every run 4 sample had the same prompt.

## Caveats

- **N = 1 per cell.**
- **Parallel.** Up to five other agents ran alongside a sample, so timings are
  not comparable with run 3's serial runs.
- **The domain favours arm A.** Story-drafting is the case the generator was shaped around.
- **s-3 still has no acceptance test in arm A.** The renderer allows one routed story per route.
- **No codex reviews yet.** That is decided after the run.
