from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestDeterministicStoryWriter:

    async def test_every_story_written_names_the_job(self) -> None:
        write_stories_response = await gateways.DeterministicStoryWriter().write_stories(
            ports.WriteStoriesRequest(job="ship the pick")
        )

        assert write_stories_response.texts != ()
        assert all("ship the pick" in text for text in write_stories_response.texts)

    async def test_the_same_job_writes_the_same_stories(self) -> None:
        deterministic_story_writer = gateways.DeterministicStoryWriter()

        first = await deterministic_story_writer.write_stories(ports.WriteStoriesRequest(job="a job"))
        again = await deterministic_story_writer.write_stories(ports.WriteStoriesRequest(job="a job"))

        assert first == again
