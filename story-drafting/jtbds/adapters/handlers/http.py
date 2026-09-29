from __future__ import annotations

import json

import tesser.adapters as ts

import jtbds.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, jtbds_client: client.JtbdsClient) -> None:
        self._jtbds_client = jtbds_client

    async def submit_jtbd(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        description = http_request.text("description")
        status = http_request.text("status")
        submit_jtbd_response = await self._jtbds_client.submit_jtbd(
            client.SubmitJtbdRequest(description=description, status=status)
        )
        return protocol.HttpResponse(
            status_code=201, body=json.dumps({"jtbd_id": submit_jtbd_response.jtbd_id}).encode()
        )

    async def check_jtbd_status(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        jtbd_id = http_request.path_param("jtbd_id")
        check_jtbd_status_response = await self._jtbds_client.check_jtbd_status(client.CheckJtbdStatusRequest(jtbd_id=jtbd_id))
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "jtbd_id": check_jtbd_status_response.job_to_be_done.jtbd_id,
                    "description": check_jtbd_status_response.job_to_be_done.description,
                    "status": check_jtbd_status_response.job_to_be_done.status,
                }
            ).encode(),
        )
