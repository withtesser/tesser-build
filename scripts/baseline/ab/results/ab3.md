# A/B run 3: both prompts ask only what the stories require (Opus and Sonnet, medium)

What changed from run 2:

- **The bare prompt.** It no longer tells the agent to build "the wait at the
  checkpoint". No story asks for it, and red never built it.
- **The specs.** Red's specs are the ones on main after #25 (the language is
  meanings only) and #26 (the level-2 stories name `stories`), on scaffold
  `story-drafting-scaffold-s8`.
- **Green's prompt.** It pastes every file red's render leaves to green (`{{AGENT_FILES}}`) instead of naming
  the drafter gateway earlier reds happened to design; this run's Opus red
  designed none.
- **The time split.** Agent time is split by what the agent was waiting on
  (`metrics.time_split`).

N = 1 per cell, medium effort, one agent definition, one run at a time (no two
agents ran together).

| | Opus A (red + green) | Opus B (bare) | Sonnet A (red + green) | Sonnet B (bare) |
|---|---|---|---|---|
| Agent time | 237.6 + 122.1 = **359.7 s** | **245.5 s** | 120.6 + 75.8 = **196.4 s** | **41.0 s** |
| Model's own time | 156.7 + 97.7 = 254.4 s | 163.1 s | 68.0 + 45.0 = 113.0 s | 22.6 s |
| Checking (gate, tests, analyzer) | 46.4 + 16.2 = 62.6 s | 10.3 s | 38.4 + 17.3 = 55.7 s | 0 s |
| Setup (venv, installs) | 6.2 s | 17.6 s | 0 s | 17.0 s |
| Probing by hand (curl, main.py) | 11.3 s | 11.3 s | 0 s | 1.4 s |
| Other tool calls | 17.1 + 8.2 = 25.3 s | 43.3 s | 14.1 + 13.5 = 27.6 s | 0 s |
| Tool calls | 14 + 12 = 26 | 29 | 9 + 6 = 15 | 5 |
| Shared check: submit, read, read after restart | pass, pass, pass | pass, pass, pass | pass, pass, pass | pass, pass, pass |
| Automated tests | 67 (gate), 88.2% impl coverage | 5 unit + an e2e script | 70 (gate), 89.6% impl coverage | none |
| Written by the agent | red: 3 specs + 2 tests; green: 4 files, 47 impl + 54 test lines | 12 files, 407 Python lines | red: 3 specs + 2 tests; green: 3 files, 78 impl lines, 0 test lines | 3 files, 152 Python lines |
| Restart tested by the agent | no (no story test can) | yes (its e2e script) | no | no |
| Unknown id / missing field | 500 / 400 | 404 / 422 | 500 / 400 | 404 / 422 |
| Durable wait at the checkpoint | no | no | no | no |

## Reading it

- **Taking out the checkpoint sentence removed the round-2 difference.**
  Neither bare agent built the durable wait. Opus B ends its workflow at the
  checkpoint because accepting is out of scope, which is the reasoning red
  gave in run 2.
- **Arm B was faster in both cells, by a lot for Sonnet.** For Opus it was
  about 114 s faster (246 s against 360 s), and 91 s of that is the model's
  own time. For Sonnet it was about 155 s faster (41 s against 196 s): five calls, no tests, and no restart
  test of its own. It passed the shared check anyway. Run 2's "arm A is about 12% faster" does
  not hold here. In run 2 most of that lead was arm B's 91 s of setup;
  here arm B's setup was about 17 s, probably a warm pip cache from the earlier
  runs (not controlled).
- **What arm A buys is still tests and conformance, not speed.** It has 67–70
  gated tests, about 88–90% implementation coverage, and 0 tessercheck
  findings. Arm B has 5 unit tests (Opus) or none (Sonnet).
- **Arm A still answers 500 for an unknown id and 400 for a missing field.**
  Both bare agents answer 404 and 422. No story names either case, so this is
  observed and not scored.
- **The two reds designed different compositions from the same specs.** Opus
  made story drafting a domain command, with no gateway. Sonnet kept a
  `CannedStoryDrafter` gateway, with a second action (`record_stories`) after
  it. Both passed.

## Harness defects this run found

1. **Green's prompt assumed red's design.** It pasted
   `template_story_drafter.py` by name, and `prepare` refused the green run when
   red designed no gateway. Fixed with `{{AGENT_FILES}}`, which also pastes the
   agent-owned store for the first time. That is a little more context than
   run 2's green had.
2. **The shared check could pass a restart that never happened.** Sonnet B's
   own test server survived its `pkill -f "main.py"`, because the Restate SDK's
   SIGTERM handler ignores the signal. It held the check's port. Every host
   the check started failed with "Address already in use", so the check drove
   the agent's leftover server, and "restarting" it restarted nothing. The
   first check of Sonnet B reported a pass it had not earned. `check.py` now
   refuses a port that answers before the check starts, and fails story 3 when
   its host has exited. Sonnet B was rechecked once its leftover server had been stopped and passed properly, with the
   check's own host on both sides of a real restart. Opus B's first check did
   not have this problem (its host did not exit early).
3. **`pkill -f "main.py"` is machine-wide.** A bare agent can kill any
   `main.py` on the machine, another session's included. That's a risk when bare runs
   go in parallel with other work.
4. **Opus red's first gate run failed on "connection refused" to its served
   host** and it ran verify again, which accounts for part of its 238 s. The
   cause is unconfirmed (nothing was listening on its ports afterwards).

## Caveats

- **N = 1 per cell.** Differences here are not evidence of a trend.
- **The runs are not comparable with runs 1 and 2.** They use different specs and a different green prompt.
- **The pip cache was not controlled** between bare runs.
- **The domain favours arm A.** Story-drafting is the case the generator was shaped
  around.
- **No cold codex reviews yet** for this run's four trees.
