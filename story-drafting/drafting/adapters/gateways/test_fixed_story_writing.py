from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestFixedStoryWriting:

    async def test_the_same_job_is_written_into_the_same_stories(self) -> None:
        fixed_story_writing = gateways.FixedStoryWriting()

        first = await fixed_story_writing.write_stories(ports.WriteStoriesRequest(job="plan a migration"))
        second = await fixed_story_writing.write_stories(ports.WriteStoriesRequest(job="plan a migration"))

        assert first == second

    async def test_every_story_written_names_the_job(self) -> None:
        write_stories_response = await gateways.FixedStoryWriting().write_stories(
            ports.WriteStoriesRequest(job="plan a migration")
        )

        assert write_stories_response.stories
        assert all("plan a migration" in story for story in write_stories_response.stories)
