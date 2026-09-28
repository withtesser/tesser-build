from __future__ import annotations

import asyncio
import typing

import tesser.srv as ts
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import restate

import app as app

_BIND: typing.Final[str] = "0.0.0.0:9080"


class RestateHost(ts.Host):

    def run(self, argv: list[str]) -> int:
        story_drafting_app = app.load()
        try:
            config = hypercorn_config.Config()
            config.bind = [argv[0] if argv else _BIND]
            served = typing.cast(
                hypercorn_typing.ASGIFramework,
                restate.app(
                    [
                        story_drafting_app.drafting.writing_actions_service,
                        story_drafting_app.drafting.drafting_actions_service,
                        story_drafting_app.drafting.drafting_orchestrator_workflow,
                    ]
                ),
            )
            asyncio.run(hypercorn_asyncio.serve(served, config))
            return 0
        finally:
            asyncio.run(story_drafting_app.close())


if __name__ == "__main__":
    ts.main(RestateHost().run)
