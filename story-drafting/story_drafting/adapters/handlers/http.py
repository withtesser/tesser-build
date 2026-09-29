from __future__ import annotations

import json

import tesser.adapters as ts

import story_drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, story_drafting_client: client.StoryDraftingClient) -> None:
        self._story_drafting_client = story_drafting_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        statement = http_request.text("statement")
        submit_jtbd_response = await self._story_drafting_client.submit_jtbd(
            client.SubmitJtbdRequest(statement=statement, step="drafting", draft_count=0, picked_draft="")
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
                    "jtbd_id": come_back_to_jtbd_response.job_to_be_done.jtbd_id,
                    "statement": come_back_to_jtbd_response.job_to_be_done.statement,
                    "step": come_back_to_jtbd_response.job_to_be_done.step,
                    "draft_count": come_back_to_jtbd_response.job_to_be_done.draft_count,
                    "picked_draft": come_back_to_jtbd_response.job_to_be_done.picked_draft,
                }
            ).encode(),
        )
