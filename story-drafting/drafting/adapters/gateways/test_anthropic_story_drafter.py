from __future__ import annotations

import pytest

import anthropic

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestAnthropicStoryDrafter:

    async def test_an_unreachable_model_fails_the_draft_loudly(self) -> None:
        async_anthropic = anthropic.AsyncAnthropic(api_key="unused", base_url="http://127.0.0.1:9", max_retries=0)

        with pytest.raises(anthropic.APIConnectionError):
            await gateways.AnthropicStoryDrafter(async_anthropic).draft_stories(
                ports.DraftStoriesRequest(job="ship a release")
            )
