from __future__ import annotations

import typing

import tesser.adapters as ts
import anthropic
import anthropic.types as anthropic_types

import drafting.application.ports as ports

_MODEL: typing.Final[str] = "claude-opus-5-5"
_MAX_TOKENS: typing.Final[int] = 16000
_SYSTEM: typing.Final[str] = (
    "You draft user stories from a job to be done. Write each story as one line in the form "
    "'As a <role>, I want <capability>, so that <benefit>.' Reply with the stories only, one per line, "
    "with no numbering, bullets, headings, or other text."
)
_BULLETS: typing.Final[str] = "-*• "


class AnthropicStoryDrafter(ts.Gateway):

    def __init__(self, async_anthropic: anthropic.AsyncAnthropic) -> None:
        self._async_anthropic = async_anthropic

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        message = await self._async_anthropic.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            messages=[{"role": "user", "content": draft_stories_request.job}],
        )
        text = "\n".join(block.text for block in message.content if isinstance(block, anthropic_types.TextBlock))
        return ports.DraftStoriesResponse(
            stories=tuple(line.strip().lstrip(_BULLETS) for line in text.splitlines() if line.strip().lstrip(_BULLETS))
        )
