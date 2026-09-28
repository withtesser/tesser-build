from __future__ import annotations

import json
import typing

import tesser.adapters as ts
import anthropic
import anthropic.types as anthropic_types

import drafting.application.ports as ports

_MODEL: typing.Final[str] = "claude-opus-5-5"
_MAX_TOKENS: typing.Final[int] = 16000
_SYSTEM: typing.Final[str] = (
    "You draft user stories for a developer from a job to be done. Write three to five user stories, each in "
    "the form 'As a <role>, I want <capability>, so that <benefit>.', each small enough to build and test on "
    "its own, together covering the job. The developer will pick which stories to accept."
)
_STORIES: typing.Final[anthropic_types.JSONOutputFormatParam] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {"stories": {"type": "array", "items": {"type": "string"}}},
        "required": ["stories"],
        "additionalProperties": False,
    },
}


class MapToComposeStoriesResponse(ts.Mapper, ports.ComposeStoriesResponse):

    def __init__(self, message: anthropic_types.Message) -> None:
        super().__init__(
            stories=tuple(
                json.loads(
                    "".join(block.text for block in message.content if isinstance(block, anthropic_types.TextBlock))
                )["stories"]
            )
        )


class AnthropicStoryDrafter(ts.Gateway):

    def __init__(self, api_key: str, base_url: str) -> None:
        self._async_anthropic = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)

    async def compose_stories(self, compose_stories_request: ports.ComposeStoriesRequest) -> ports.ComposeStoriesResponse:
        message = await self._async_anthropic.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            messages=[{"role": "user", "content": compose_stories_request.job}],
            output_config={"format": _STORIES},
        )
        return MapToComposeStoriesResponse(message)
