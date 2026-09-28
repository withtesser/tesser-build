from __future__ import annotations

import json
import typing

import tesser.application as ts


class KeepDraftedStoriesRequest(ts.Request):

    def __init__(self, drafting_id: str, job: str, texts: tuple[str, ...]) -> None:
        self.drafting_id = drafting_id
        self.job = job
        self.texts = texts


class KeepDraftedStoriesRequestSnapshot(ts.Serde):

    def serialize(self, keep_drafted_stories_request: KeepDraftedStoriesRequest) -> bytes:
        return json.dumps(
            {
                "drafting_id": keep_drafted_stories_request.drafting_id,
                "job": keep_drafted_stories_request.job,
                "texts": list(keep_drafted_stories_request.texts),
            }
        ).encode()

    def deserialize(self, buf: bytes) -> KeepDraftedStoriesRequest:
        snapshot = json.loads(buf)
        return KeepDraftedStoriesRequest(
            drafting_id=snapshot["drafting_id"], job=snapshot["job"], texts=tuple(snapshot["texts"])
        )


class KeepDraftedStoriesResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class KeepDraftedStoriesResponseSnapshot(ts.Serde):

    def serialize(self, keep_drafted_stories_response: KeepDraftedStoriesResponse) -> bytes:
        return json.dumps({"drafting_id": keep_drafted_stories_response.drafting_id}).encode()

    def deserialize(self, buf: bytes) -> KeepDraftedStoriesResponse:
        snapshot = json.loads(buf)
        return KeepDraftedStoriesResponse(drafting_id=snapshot["drafting_id"])


class DraftingActionsRelay(ts.Relay, typing.Protocol):

    async def run_keep_drafted_stories(
        self, keep_drafted_stories_request: KeepDraftedStoriesRequest
    ) -> KeepDraftedStoriesResponse: ...
