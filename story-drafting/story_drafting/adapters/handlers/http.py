from __future__ import annotations

import json

import tesser.adapters as ts

import story_drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, story_drafting_client: client.StoryDraftingClient) -> None:
        self._story_drafting_client = story_drafting_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        job = http_request.text("job")
        submit_jtbd_response = await self._story_drafting_client.submit_jtbd(
            client.SubmitJtbdRequest(job=job)
        )
        return protocol.HttpResponse(
            status_code=201, body=json.dumps({"jtbd_id": submit_jtbd_response.jtbd_id}).encode()
        )

    async def come_back_to_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        jtbd_id = http_request.path_param("jtbd_id")
        come_back_to_jtbd_response = await self._story_drafting_client.come_back_to_jtbd(client.ComeBackToJtbdRequest(jtbd_id=jtbd_id))
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "jtbd_id": come_back_to_jtbd_response.jtbd.jtbd_id,
                    "job": come_back_to_jtbd_response.jtbd.job,
                }
            ).encode(),
        )
