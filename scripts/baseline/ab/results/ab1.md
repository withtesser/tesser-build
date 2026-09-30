# A/B run 1: the tesser pipeline against a bare agent (story-drafting)

N = 1 per cell. Medium effort everywhere; every agent is the same definition
(`tesser-red-trial-medium`, system prompt hash `a103749a015bf39e`; see each
record's `conditions`). Arm B was given the same Restate server and told so
(a documented deviation: the generator picks that engine silently and no spec
asks the user). Red and arm B ran at the same time on one machine; green ran
alone.

| | Opus A (red + green) | Opus B (bare) | Sonnet A (red + green) | Sonnet B (bare) |
|---|---|---|---|---|
| Agent time | 110.5 s + 143.4 s = **253.9 s** | **275.9 s** | 113.6 s + 116.4 s = **230.0 s** | **92.9 s** |
| Tool calls | 5 + 16 = 21 | 29 | 7 + 12 = 19 | 11 |
| Shared check (both stories over HTTP) | pass | pass | pass | pass |
| Automated tests | 79 (gate) | 7 (unit, domain only) | 71 (gate) | 0 |
| Implementation coverage | 90.0% | about 36% (routes, workflow, server 0%) | 89.8% | 0% |
| Acceptance tests for the two stories | 2, through the served host | none (checked by hand) | 2 | none |
| Files / Python lines written by the agent | red: specs + 2 tests; green: 4 files, 70 impl + 93 test lines | 10 files, 320 lines | red: specs + 2 tests; green: 4 files, 35 impl + 13 test lines | 4 files, 115 lines |
| Tree it leaves | 69 Python files, 61 generated, layered | 5 modules + main | same as Opus A | 2 modules |
| Durable wait at the checkpoint | no (red dropped the signal) | yes (Restate promise) | no | yes (Restate promise) |
| tessercheck | 0 findings, integrity ok | not applicable | 0 findings (4,1,1,0,0 while working), integrity ok | not applicable |

## Reading it

- **Speed is not the pipeline's advantage.** Opus is roughly a tie; bare Sonnet
  is about 2.5 times faster than Sonnet's red + green. N = 1, and the story-
  drafting example was the one the generator was shaped around, so this
  favours arm A if anything.
- **What arm A leaves that arm B does not:** automated acceptance tests for both
  stories, about 90% implementation coverage against 0-36%, a layered tree
  with an enforced import direction, and zero analyzer findings.
- **What arm B has that arm A does not:** the durable wait at the checkpoint.
  Red dropped the signal in every trial because no story names it (the
  level-1 story wants checkpoints that survive across sessions, which is a
  story gap or a scope decision for the story owner).
- **Not measured:** durability across a restart (no story restarts anything),
  gate and setup time (not timed), involvement (zero for both: the specs and
  the prose were given).

## Defects the runs found

- A generated relay test
  (`test_restate_http_jtbd_orchestrator_relay.py::test_start_..._does_not_wait`)
  asserts the workflow is not yet completed after a 0.1 s poll, and fails
  when green's drafter lets the workflow finish first. It failed on the first
  full run in both green phases and passed on rerun. Together with two other
  non-root flakes earlier that is about three in 14 gate runs.
- Green makes 12-16 calls: a double Read of a 75 KB prompt, a `git status` the
  prompt forbids, exploratory finds and greps, a patch to a file it had just
  written, and reruns caused by the flaky test.

## Caveats

- One run per cell; nothing here separates skill from noise.
- Red and arm B shared the machine while running.
- The check is tolerant by design; it asserts only what the two stories say.
