# A/B: the tesser pipeline against a bare agent (story-drafting)

Same product, two ways. **Arm A** is red then green from three specs
(`story-drafting/specs/language.toml`, `story.toml`, `infra.toml`: what the
product means, what a user must be able to do, and what it runs on) on the
current story-drafting scaffold. **Arm B** is one bare agent in an empty
repository outside this tree, given `prompts/bare.md`: the same facts as the
three specs in prose (fidelity-reviewed against them, twice), and nothing else
except the disclosed harness facts (the port it must listen on, `.venv`, the
checker, and what a restart means).

Every agent in both arms is the same definition (`~/.claude/agents/tesser-red-trial-medium.md`:
effort medium, one generic body; the model is passed per call), spawned unnamed
so the definition's effort applies, so all runs share one system prompt. The same check (`check.py`) runs on each
arm's output: it serves the output, registers the Restate endpoint, and drives
the two level-2 stories over HTTP, tolerant of what the specs leave open (id
shape, extra keys, how long drafting takes).

    scripts/baseline/ab/prepare-bare <run> <slot>          # arm B
    scripts/baseline/ab/measure-bare <run> <transcript>    # arm B: metrics + check
    scripts/baseline/ab/check-tree A|B <run>               # the shared check, alone

Arm A uses the existing `prepare red-specs ...`, `prepare green-on-red <red
branch> ...`, `measure`, then `check-tree A <green run>`.

Reported per arm: agent time and calls per phase, gate time and Restate setup
separately, the shared check's result, files and lines. Not measured: durability
across a restart (no story restarts anything).
