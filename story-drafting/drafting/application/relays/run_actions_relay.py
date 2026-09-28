from __future__ import annotations

import json
import typing

import tesser.application as ts


class KeepRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class KeepRunRequestSnapshot(ts.Serde):

    def serialize(self, keep_run_request: KeepRunRequest) -> bytes:
        return json.dumps({"run_id": keep_run_request.run_id, "job": keep_run_request.job}).encode()

    def deserialize(self, buf: bytes) -> KeepRunRequest:
        snapshot = json.loads(buf)
        return KeepRunRequest(run_id=snapshot["run_id"], job=snapshot["job"])


class KeepRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class KeepRunResponseSnapshot(ts.Serde):

    def serialize(self, keep_run_response: KeepRunResponse) -> bytes:
        return json.dumps({"run_id": keep_run_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> KeepRunResponse:
        snapshot = json.loads(buf)
        return KeepRunResponse(run_id=snapshot["run_id"])


class OfferStoriesRequest(ts.Request):

    def __init__(self, run_id: str, job: str, stories: tuple[str, ...]) -> None:
        self.run_id = run_id
        self.job = job
        self.stories = stories


class OfferStoriesRequestSnapshot(ts.Serde):

    def serialize(self, offer_stories_request: OfferStoriesRequest) -> bytes:
        return json.dumps(
            {
                "run_id": offer_stories_request.run_id,
                "job": offer_stories_request.job,
                "stories": list(offer_stories_request.stories),
            }
        ).encode()

    def deserialize(self, buf: bytes) -> OfferStoriesRequest:
        snapshot = json.loads(buf)
        return OfferStoriesRequest(run_id=snapshot["run_id"], job=snapshot["job"], stories=tuple(snapshot["stories"]))


class OfferStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class OfferStoriesResponseSnapshot(ts.Serde):

    def serialize(self, offer_stories_response: OfferStoriesResponse) -> bytes:
        return json.dumps({"run_id": offer_stories_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> OfferStoriesResponse:
        snapshot = json.loads(buf)
        return OfferStoriesResponse(run_id=snapshot["run_id"])


class RunActionsRelay(ts.Relay, typing.Protocol):

    async def run_keep_run(self, keep_run_request: KeepRunRequest) -> KeepRunResponse: ...

    async def run_offer_stories(self, offer_stories_request: OfferStoriesRequest) -> OfferStoriesResponse: ...
