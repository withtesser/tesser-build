# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import asyncio
import os
import sys
import traceback
import typing

import tesser.srv as ts
import fastapi
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import restate

import app as app
import drafting.adapters.handlers as drafting_handlers
import protocol

_LISTEN_PORT_VARIABLE: typing.Final[str] = "STORY_DRAFTING_PORT"
_RESTATE_DEPLOYMENT_PATH: typing.Final[str] = "/restate"
_JSON: typing.Final[str] = "application/json"


class HttpRoutes(ts.Host):

    def __init__(self, http_handler: drafting_handlers.HttpHandler) -> None:
        self._http_handler = http_handler

    async def submit_jtbd(self, request: fastapi.Request) -> fastapi.Response:
        try:
            http_response = await self._http_handler.submit_jtbd(
                protocol.HttpRequest(path_params=request.path_params, body=await request.body())
            )
        except protocol.BadRequest as error:
            http_response = protocol.HttpResponse.problem(400, str(error))
        except Exception:
            traceback.print_exc(file=sys.stderr)
            http_response = protocol.HttpResponse.problem(500, "unexpected error")
        return fastapi.Response(http_response.body, http_response.status_code, media_type=_JSON)

    async def get_jtbd(self, request: fastapi.Request) -> fastapi.Response:
        try:
            http_response = await self._http_handler.get_jtbd(
                protocol.HttpRequest(path_params=request.path_params, body=await request.body())
            )
        except protocol.BadRequest as error:
            http_response = protocol.HttpResponse.problem(400, str(error))
        except Exception:
            traceback.print_exc(file=sys.stderr)
            http_response = protocol.HttpResponse.problem(500, "unexpected error")
        return fastapi.Response(http_response.body, http_response.status_code, media_type=_JSON)


class HttpHost(ts.Host):

    def run(self, argv: list[str]) -> int:
        story_drafting_app = app.load()
        http_routes = HttpRoutes(drafting_handlers.HttpHandler(story_drafting_app.drafting.client))
        api = fastapi.FastAPI()
        api.add_api_route("/jtbds", http_routes.submit_jtbd, methods=["POST"])
        api.add_api_route("/jtbds/{jtbd_id}", http_routes.get_jtbd, methods=["GET"])
        api.mount(
            _RESTATE_DEPLOYMENT_PATH,
            restate.app(
                [
                    story_drafting_app.drafting.story_actions_service,
                    story_drafting_app.drafting.jtbd_actions_service,
                    story_drafting_app.drafting.jtbd_orchestrator_workflow,
                ]
            ),
        )
        config = hypercorn_config.Config()
        config.bind = [argv[0] if argv else f"0.0.0.0:{os.environ[_LISTEN_PORT_VARIABLE]}"]
        served = typing.cast(hypercorn_typing.ASGIFramework, api)
        with asyncio.Runner() as runner:
            runner.run(story_drafting_app.open())
            try:
                runner.run(hypercorn_asyncio.serve(served, config))
            finally:
                runner.run(story_drafting_app.close())
        return 0


if __name__ == "__main__":
    ts.main(HttpHost().run)
