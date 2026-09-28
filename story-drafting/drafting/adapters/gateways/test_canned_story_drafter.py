from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestCannedStoryDrafter:

    async def test_the_same_job_drafts_the_same_stories_each_naming_the_job(self) -> None:
        canned_story_drafter = gateways.CannedStoryDrafter()
        first = await canned_story_drafter.compose_stories(ports.ComposeStoriesRequest(job="ship a release"))
        second = await canned_story_drafter.compose_stories(ports.ComposeStoriesRequest(job="ship a release"))
        assert first == second
        assert first.stories != ()
        assert all("ship a release" in story for story in first.stories)
