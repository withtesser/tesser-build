from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestDeterministicStoryDrafter:

    async def test_the_same_job_drafts_the_same_stories(self) -> None:
        deterministic_story_drafter = gateways.DeterministicStoryDrafter()

        first = await deterministic_story_drafter.draft_stories(ports.DraftStoriesRequest(job="ship a release"))
        second = await deterministic_story_drafter.draft_stories(ports.DraftStoriesRequest(job="ship a release"))

        assert first == second

    async def test_every_drafted_story_is_about_the_job(self) -> None:
        draft_stories_response = await gateways.DeterministicStoryDrafter().draft_stories(
            ports.DraftStoriesRequest(job="ship a release")
        )

        assert draft_stories_response.stories != ()
        assert all("ship a release" in story for story in draft_stories_response.stories)
