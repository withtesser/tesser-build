from __future__ import annotations

import json
import typing

import tesser.adapters as ts
import anthropic

import drafting.application.ports as ports

_MODEL: typing.Final[str] = "claude-opus-5-5"
_MAX_TOKENS: typing.Final[int] = 16000
_END_TURN: typing.Final[str] = "end_turn"
_SYSTEM: typing.Final[str] = (
    "You draft user stories for a developer. Given a job to be done, write between three and six "
    "user stories that together deliver it. Write each story as one sentence in the form "
    "'As a <role>, I want <capability>, so that <outcome>.'"
)


class AnthropicStoryWriter(ts.Gateway):

    def __init__(self, async_anthropic: anthropic.AsyncAnthropic) -> None:
        self._async_anthropic = async_anthropic

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        message = await self._async_anthropic.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            messages=[{"role": "user", "content": write_stories_request.job}],
            output_config={
                "effort": "medium",
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {"stories": {"type": "array", "items": {"type": "string"}}},
                        "required": ["stories"],
                        "additionalProperties": False,
                    },
                },
            },
        )
        if message.stop_reason != _END_TURN:
            return ports.WriteStoriesResponse(stories=())
        drafted = json.loads("".join(block.text for block in message.content if block.type == "text"))
        return ports.WriteStoriesResponse(stories=tuple(drafted["stories"]))
