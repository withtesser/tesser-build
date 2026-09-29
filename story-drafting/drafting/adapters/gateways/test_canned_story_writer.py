from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestCannedStoryWriter:

    async def test_the_same_job_is_always_written_as_the_same_stories_naming_it(self) -> None:
        first = await gateways.CannedStoryWriter().write_stories(ports.WriteStoriesRequest(job="ship the release"))
        again = await gateways.CannedStoryWriter().write_stories(ports.WriteStoriesRequest(job="ship the release"))
        assert first == again
        assert first.stories
        assert all("ship the release" in story for story in first.stories)
