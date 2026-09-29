from __future__ import annotations

import json

import tesser.adapters as ts

import drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        status = http_request.text("status")
        submit_jtbd_response = await self._drafting_client.submit_jtbd(
            client.SubmitJtbdRequest(status=status)
        )
        return protocol.HttpResponse(
            status_code=201, body=json.dumps({"jtbd_id": submit_jtbd_response.jtbd_id}).encode()
        )

    async def check_jtbd_status(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        jtbd_id = http_request.path_param("jtbd_id")
        check_jtbd_status_response = await self._drafting_client.check_jtbd_status(client.CheckJtbdStatusRequest(jtbd_id=jtbd_id))
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "jtbd_id": check_jtbd_status_response.jtbd.jtbd_id,
                    "status": check_jtbd_status_response.jtbd.status,
                }
            ).encode(),
        )
