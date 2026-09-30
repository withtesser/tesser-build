# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json

import tesser.adapters as ts

import drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        submit_jtbd_response = await self._drafting_client.submit_jtbd(
            client.SubmitJtbdRequest(
                role=http_request.text("role"),
                i_want=http_request.text("i_want"),
                so_that=http_request.text("so_that"),
            )
        )
        return protocol.HttpResponse(
            status_code=201,
            body=json.dumps(
                {
                    "jtbd_id": submit_jtbd_response.jtbd_id,
                    "status": submit_jtbd_response.status,
                }
            ).encode(),
        )

    async def get_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        get_jtbd_response = await self._drafting_client.get_jtbd(
            client.GetJtbdRequest(
                jtbd_id=http_request.path_param("jtbd_id"),
            )
        )
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "status": get_jtbd_response.status,
                    "stories": [{"given": story.given, "when": story.when, "then": story.then, "state": story.state} for story in get_jtbd_response.stories],
                }
            ).encode(),
        )
