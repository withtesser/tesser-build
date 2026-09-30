from __future__ import annotations

import asyncio
import typing

import anthropic
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports
import simulated.messages_api as simulated_messages_api


class TestAnthropicStoryWriter:

    async def test_the_job_goes_to_the_model_and_the_stories_it_drafts_come_back(self, free_port: int) -> None:
        messages_api = simulated_messages_api.MessagesApi()
        port = free_port
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"127.0.0.1:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, messages_api),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        try:
            write_stories_response = ports.WriteStoriesResponse(stories=())
            for _ in range(50):
                try:
                    write_stories_response = await gateways.AnthropicStoryWriter(
                        anthropic.AsyncAnthropic(api_key="simulated", base_url=f"http://127.0.0.1:{port}", max_retries=0)
                    ).write_stories(ports.WriteStoriesRequest(job="ship the release"))
                    break
                except anthropic.APIConnectionError:
                    await asyncio.sleep(0.1)
        finally:
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
        assert write_stories_response == ports.WriteStoriesResponse(stories=simulated_messages_api.STORIES)
        assert [request["messages"] for request in messages_api.requests] == [
            [{"role": "user", "content": "ship the release"}]
        ]
