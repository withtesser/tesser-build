from __future__ import annotations

import socket

import anthropic
import pytest

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestAnthropicStoryDrafter:

    async def test_a_draft_goes_to_the_messages_api_it_was_given_and_fails_loudly_when_nothing_answers(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        anthropic_story_drafter = gateways.AnthropicStoryDrafter(api_key="unused", base_url=f"http://127.0.0.1:{port}")
        with pytest.raises(anthropic.APIConnectionError):
            await anthropic_story_drafter.compose_stories(ports.ComposeStoriesRequest(job="a job"))
