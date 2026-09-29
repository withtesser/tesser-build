from __future__ import annotations

import json

import tesser.adapters as ts

import drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        situation = http_request.text("situation")
        motivation = http_request.text("motivation")
        outcome = http_request.text("outcome")
        submit_jtbd_response = await self._drafting_client.submit_jtbd(
            client.SubmitJtbdRequest(situation=situation, motivation=motivation, outcome=outcome)
        )
        return protocol.HttpResponse(
            status_code=201, body=json.dumps({"jtbd_id": submit_jtbd_response.jtbd_id}).encode()
        )

    async def check_status(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        jtbd_id = http_request.path_param("jtbd_id")
        check_status_response = await self._drafting_client.check_status(client.CheckStatusRequest(jtbd_id=jtbd_id))
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "jtbd_id": check_status_response.jtbd.jtbd_id,
                    "situation": check_status_response.jtbd.situation,
                    "motivation": check_status_response.jtbd.motivation,
                    "outcome": check_status_response.jtbd.outcome,
                }
            ).encode(),
        )
