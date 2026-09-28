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
    "You draft user stories from a job to be done. Each story reads "
    "'As a <role>, I want <capability>, so that <benefit>.' Draft between three and six "
    "stories that together deliver the job, each one small enough to build and check on its own."
)
_OUTPUT_CONFIG: typing.Final[anthropic_types.OutputConfigParam] = {
    "effort": "low",
    "format": {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {"stories": {"type": "array", "items": {"type": "string"}}},
            "required": ["stories"],
            "additionalProperties": False,
        },
    },
}


class MapToWriteStoriesResponse(ts.Mapper, ports.WriteStoriesResponse):

    def __init__(self, message: anthropic_types.Message) -> None:
        drafted = json.loads("".join(block.text for block in message.content if block.type == "text"))
        super().__init__(stories=tuple(drafted["stories"]))


class AnthropicStoryWriting(ts.Gateway):

    def __init__(self, async_anthropic: anthropic.AsyncAnthropic) -> None:
        self._async_anthropic = async_anthropic

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        message = await self._async_anthropic.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            output_config=_OUTPUT_CONFIG,
            messages=[{"role": "user", "content": write_stories_request.job}],
        )
        return MapToWriteStoriesResponse(message)
