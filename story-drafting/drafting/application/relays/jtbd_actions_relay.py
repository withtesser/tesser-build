# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class JtbdActionsStoryText(ts.Response):

    def __init__(self, given: str, when: str, then: str) -> None:
        self.given = given
        self.when = when
        self.then = then


class RecordDraftedStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str, story_texts: tuple[JtbdActionsStoryText, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that
        self.story_texts = story_texts


class RecordDraftedStoriesRequestSnapshot(ts.Serde):

    def serialize(self, record_drafted_stories_request: RecordDraftedStoriesRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": record_drafted_stories_request.jtbd_id,
                "role": record_drafted_stories_request.role,
                "i_want": record_drafted_stories_request.i_want,
                "so_that": record_drafted_stories_request.so_that,
                "story_texts": [{"given": story_text.given, "when": story_text.when, "then": story_text.then} for story_text in record_drafted_stories_request.story_texts],
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordDraftedStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("role"), str)
            and isinstance(snapshot.get("i_want"), str)
            and isinstance(snapshot.get("so_that"), str)
            and isinstance(snapshot.get("story_texts"), list)
            and all(isinstance(story_text, dict) and isinstance(story_text.get("given"), str) and isinstance(story_text.get("when"), str) and isinstance(story_text.get("then"), str) for story_text in snapshot["story_texts"])
        ):
            raise errors.invalid("invalid_snapshot", "a record drafted stories request is its jtbd_id, role, i_want, so_that, and story_texts")
        return RecordDraftedStoriesRequest(
            jtbd_id=snapshot["jtbd_id"],
            role=snapshot["role"],
            i_want=snapshot["i_want"],
            so_that=snapshot["so_that"],
            story_texts=tuple(JtbdActionsStoryText(given=story_text["given"], when=story_text["when"], then=story_text["then"]) for story_text in snapshot["story_texts"]),
        )


class RecordDraftedStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class RecordDraftedStoriesResponseSnapshot(ts.Serde):

    def serialize(self, record_drafted_stories_response: RecordDraftedStoriesResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": record_drafted_stories_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordDraftedStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a record drafted stories response is its jtbd_id")
        return RecordDraftedStoriesResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_record_drafted_stories(self, record_drafted_stories_request: RecordDraftedStoriesRequest) -> RecordDraftedStoriesResponse: ...
