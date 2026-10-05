# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root (the glossary). It does not exist yet; the `/domain-modeling` skill creates it lazily when terms get resolved.
- **`docs/design-*.md`**: this repo's decision records. Each one carries the reasoning behind a convention family (e.g. `docs/design-app-service-types.md`, `docs/design-test-tiers.md`, `docs/design-repo-layout.md`). Read the ones that touch the area you're about to work in. There is no `docs/adr/` directory; treat these design docs as the ADRs.
- **The brain at `~/workspace/brain`**: the deeper rationale and provenance behind the conventions, outside this repo. Start with `originals/changeability-silent-site-cost.md` and `originals/obligations-conformance-changeability.md`; use `gbrain search "<terms>"` for semantic lookups across it.
- **gstack design docs at `~/.gstack/projects/verocorp-tesser-build/`** (the repo's pre-rename gstack slug; `withtesser-tesser-build/` holds no docs yet): office-hours and plan-review output — `*-design-*.md`, `*-test-plan-*.md`, `error-norms-design-*.md` — plus `decisions.active.json` / `decisions.jsonl` (recorded decisions with rationale) and `learnings.jsonl`. Older entries date from the Go predecessor; where one disagrees with a `docs/design-*.md` or the current code, the repo wins.

If any of these don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront.

## Where new decisions go

A decision that belongs to an existing convention family goes into that family's `docs/design-*.md`. A new family gets a new `docs/design-<topic>.md`. Do not create `docs/adr/`. Glossary terms go in a root `CONTEXT.md` (single-context repo).

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md` and the design docs. Don't drift to synonyms they explicitly avoid.

If the concept you need isn't defined yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag decision conflicts

If your output contradicts an existing design doc, surface it explicitly rather than silently overriding:

> _Contradicts `docs/design-test-tiers.md` (placement carries the tier), but worth reopening because…_
