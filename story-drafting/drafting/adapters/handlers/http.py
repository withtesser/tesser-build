from __future__ import annotations

import json

import tesser.adapters as ts

import drafting.client as client
import protocol as protocol


class HttpHandler(ts.Handler):

    def __init__(self, drafting_client: client.DraftingClient) -> None:
        self._drafting_client = drafting_client

    async def open_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        open_run_response = await self._drafting_client.open_run(
            client.OpenRunRequest(job=http_request.text("job"))
        )
        return protocol.HttpResponse(
            status_code=202, body=json.dumps({"run_id": open_run_response.run_id}).encode()
        )

    async def get_run(self, http_request: protocol.HttpRequest) -> protocol.HttpResponse:
        run_id = http_request.path_param("run_id")
        get_run_response = await self._drafting_client.get_run(client.GetRunRequest(run_id=run_id))
        if not get_run_response.runs:
            return protocol.HttpResponse.problem(404, f"no run {run_id}")
        return protocol.HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "run_id": get_run_response.runs[0].run_id,
                    "job": get_run_response.runs[0].job,
                    "stage": get_run_response.runs[0].stage,
                }
            ).encode(),
        )
