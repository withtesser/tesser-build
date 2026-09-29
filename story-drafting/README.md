# story-drafting

The story-drafting skill, as a scaffold for the green track: the tree the
composition-driven renderer writes from `generator/compositions/story-drafting/`,
plus two root acceptance tests written by hand. A developer submits a job to be
done; the skill drafts its stories on a durable Restate workflow and then waits,
durably, for the developer to accept them.

```sh
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.render compositions/story-drafting ../story-drafting
```

The specs say what is built: `language.toml` (the words), `story.toml` (the
stories), `composition.toml` (the contracts), `implementations.toml` (what
satisfies each contract, where), `generator.toml` (sample values).

## Who owns what

Every rendered file's first line says so.

- `# pragma: tesser-generated` — the renderer's; render again to change it.
- `# pragma: tesser-agent-owned` — rendered once as a stub, then the green
  agent's: the aggregate's domain module (`drafting/domain/`, whose rendered
  part is the contract — `JtbdSpec`, `record_stories` and its outcomes, the
  reads) and `TemplateStoryDrafter` (`drafting/adapters/gateways/`), each with
  its test. The stubs answer minimally: `record_stories` answers
  `none_given`, `status` reads `drafting_stories`, the drafter drafts nothing.

The root acceptance tests (`tests/test_submitting_jtbds.py`, `tests/test_reading_jtbds.py`) are neither; they are the stories
(`s-1-a-1`, `s-2-a-1` in `story.toml`), and drive only the served host.

## Out of scope

Accepting stories (and so rejecting the rest), revising a job to be done's
stories, story drafting with a language model, and the agent-facing skill
document.
