from __future__ import annotations

import asyncio
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
import protocol as protocol

_BIND: typing.Final[str] = "0.0.0.0:8000"
_RESTATE_DEPLOYMENT_PATH: typing.Final[str] = "/restate"
_JSON: typing.Final[str] = "application/json"


class HttpHost(ts.Host):

    def run(self, argv: list[str]) -> int:
        story_drafting_app = app.load()
        try:
            handler = drafting_handlers.Handler(story_drafting_app.drafting.client)
            router = fastapi.APIRouter()

            @router.post("/runs")
            async def begin_run(request: fastapi.Request) -> fastapi.Response:  # tesser:debt TB023
                try:
                    http_response = await handler.begin_run(
                        protocol.HttpRequest(body=await request.body(), parameters={})
                    )
                except protocol.BadRequest as e:
                    http_response = protocol.HttpResponse.problem(400, str(e))
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    http_response = protocol.HttpResponse.problem(500, "unexpected error")
                return fastapi.Response(http_response.body, http_response.status_code, media_type=_JSON)

            @router.get("/runs/{run_id}")
            async def get_run(request: fastapi.Request, run_id: str) -> fastapi.Response:  # tesser:debt TB023
                try:
                    http_response = await handler.get_run(
                        protocol.HttpRequest(body=await request.body(), parameters={"run_id": run_id})
                    )
                except protocol.BadRequest as e:
                    http_response = protocol.HttpResponse.problem(400, str(e))
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    http_response = protocol.HttpResponse.problem(500, "unexpected error")
                return fastapi.Response(http_response.body, http_response.status_code, media_type=_JSON)

            api = fastapi.FastAPI()
            api.include_router(router)
            api.mount(
                _RESTATE_DEPLOYMENT_PATH,
                restate.app(
                    [
                        story_drafting_app.drafting.run_actions_service,
                        story_drafting_app.drafting.run_orchestrator_workflow,
                    ]
                ),
            )

            config = hypercorn_config.Config()
            config.bind = [argv[0] if argv else _BIND]
            served = typing.cast(hypercorn_typing.ASGIFramework, api)
            asyncio.run(hypercorn_asyncio.serve(served, config))
            return 0
        finally:
            story_drafting_app.close()


if __name__ == "__main__":
    ts.main(HttpHost().run)
