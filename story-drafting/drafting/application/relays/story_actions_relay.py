# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, role: str) -> None:
        self.role = role


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {
                "role": draft_stories_request.role,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("role"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a draft stories request is its role")
        return DraftStoriesRequest(
            role=snapshot["role"],
        )


class StoryText(ts.Response):

    def __init__(self, given: str, when: str, then: str) -> None:
        self.given = given
        self.when = when
        self.then = then


class DraftStoriesResponse(ts.Response):

    def __init__(self, story_texts: tuple[StoryText, ...]) -> None:
        self.story_texts = story_texts


class DraftStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_stories_response: DraftStoriesResponse) -> bytes:
        return json.dumps(
            {
                "story_texts": [{"given": story_text.given, "when": story_text.when, "then": story_text.then} for story_text in draft_stories_response.story_texts],
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("story_texts"), list)
            and all(isinstance(story_text, dict) and isinstance(story_text.get("given"), str) and isinstance(story_text.get("when"), str) and isinstance(story_text.get("then"), str) for story_text in snapshot["story_texts"])
        ):
            raise errors.invalid("invalid_snapshot", "a draft stories response is its story_texts")
        return DraftStoriesResponse(
            story_texts=tuple(StoryText(given=story_text["given"], when=story_text["when"], then=story_text["then"]) for story_text in snapshot["story_texts"]),
        )


class StoryActionsRelay(ts.Relay, typing.Protocol):

    async def run_draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...
