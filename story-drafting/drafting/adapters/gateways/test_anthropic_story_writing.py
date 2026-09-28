from __future__ import annotations

import anthropic
import httpx2

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports
import simulated.messages_api as simulated_messages_api


class TestAnthropicStoryWriting:

    async def test_the_stories_the_model_answers_come_back_as_the_stories_written(self) -> None:
        messages_api = simulated_messages_api.MessagesApi()
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(messages_api.handle)) as async_client:
            anthropic_story_writing = gateways.AnthropicStoryWriting(
                anthropic.AsyncAnthropic(api_key="test-key", http_client=async_client)
            )

            write_stories_response = await anthropic_story_writing.write_stories(
                ports.WriteStoriesRequest(job="plan a migration")
            )

        assert write_stories_response.stories == ("As a developer, I want plan a migration",)

    async def test_the_job_goes_to_the_model_asking_for_stories_under_a_json_schema(self) -> None:
        messages_api = simulated_messages_api.MessagesApi()
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(messages_api.handle)) as async_client:
            anthropic_story_writing = gateways.AnthropicStoryWriting(
                anthropic.AsyncAnthropic(api_key="test-key", http_client=async_client)
            )

            await anthropic_story_writing.write_stories(ports.WriteStoriesRequest(job="plan a migration"))

        assert [
            (received["messages"], received["output_config"]["format"]["type"])  # type: ignore[index]
            for received in messages_api.received
        ] == [([{"role": "user", "content": "plan a migration"}], "json_schema")]
