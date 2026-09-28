from __future__ import annotations

import json
import typing

import tesser.adapters as ts

import drafting.client as client
import protocol as protocol


class Handler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def begin_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        try:
            begin_run_response = await self._drafting_client.begin_run(
                client.BeginRunRequest(run_id=http_request.text("run_id"), job=http_request.text("job"))
            )
        except client.ERRORS as error:
            match error:
                case client.RunRejected():
                    return protocol.HttpResponse.problem(422, error.message)
                case client.RunNotFound():
                    return protocol.HttpResponse.problem(404, error.message)
                case _ as never:
                    typing.assert_never(never)
        return protocol.HttpResponse(
            status_code=202, body=json.dumps({"run_id": begin_run_response.run_id}).encode()
        )

    async def get_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        try:
            get_run_response = await self._drafting_client.get_run(
                client.GetRunRequest(run_id=http_request.parameter("run_id"))
            )
        except client.ERRORS as error:
            match error:
                case client.RunRejected():
                    return protocol.HttpResponse.problem(422, error.message)
                case client.RunNotFound():
                    return protocol.HttpResponse.problem(404, error.message)
                case _ as never:
                    typing.assert_never(never)
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "run_id": get_run_response.run_id,
                    "job": get_run_response.job,
                    "stage": get_run_response.stage,
                    "stories": [{"text": story.text} for story in get_run_response.stories],
                    "accepted_stories": [{"text": story.text} for story in get_run_response.accepted_stories],
                }
            ).encode(),
        )
