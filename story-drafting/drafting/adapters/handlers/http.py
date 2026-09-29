from __future__ import annotations

import json

import tesser.adapters as ts

import drafting.client as client
import protocol


class HttpHandler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def begin_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        job = http_request.text("job")
        begin_run_response = await self._drafting_client.begin_run(
            client.BeginRunRequest(job=job)
        )
        return protocol.HttpResponse(
            status_code=201, body=json.dumps({"run_id": begin_run_response.run_id}).encode()
        )

    async def get_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        run_id = http_request.path_param("run_id")
        get_run_response = await self._drafting_client.get_run(client.GetRunRequest(run_id=run_id))
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "run_id": get_run_response.run.run_id,
                    "job": get_run_response.run.job,
                }
            ).encode(),
        )
