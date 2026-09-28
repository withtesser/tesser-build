from __future__ import annotations

import asyncio
import json
import os
import socket
import typing
import uuid

import tesser.testing as ts
import httpx
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import pytest
import restate
import restate.client as restate_client

import drafting.adapters.activities as activities
import drafting.adapters.workflows as workflows
import drafting.application.client as client
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        self._steps.append(f"kept {keep_run_request.job}")
        return relays.KeepRunResponse(run_id=keep_run_request.run_id)

    async def offer_stories(self, offer_stories_request: relays.OfferStoriesRequest) -> relays.OfferStoriesResponse:
        self._steps.append(f"offered {list(offer_stories_request.stories)}")
        return relays.OfferStoriesResponse(run_id=offer_stories_request.run_id)


@ts.fake
class FakeDrafterApplicationClient(client.DrafterApplicationClient):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self._steps.append(f"wrote stories for {write_stories_request.job}")
        return relays.WriteStoriesResponse(stories=("a story", "another story"))


class TestRestateDraftStories:

    async def test_draft_stories_offers_the_drafted_stories_then_waits_on_the_promise_the_relays_name(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        drafter_actions_service = restate.Service(f"DrafterActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        steps: list[str] = []
        fake_run_application_client = FakeRunApplicationClient(steps)
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateKeepRun(run_actions_service, fake_run_application_client),
            activities.RestateOfferStories(run_actions_service, fake_run_application_client),
            activities.RestateWriteStories(drafter_actions_service, FakeDrafterApplicationClient(steps)),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(
                    hypercorn_typing.ASGIFramework,
                    restate.app([run_actions_service, drafter_actions_service, run_orchestrator_workflow]),
                ),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            for _ in range(50):
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['STORY_DRAFTING_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                sent = await restate_client.Client(async_client).workflow_send(
                    restate_draft_stories.handler,
                    key=run_id,
                    arg=relays.DraftStoriesRequest(run_id=domain.RunId(run_id), job=domain.Job("a job")),
                )
            awaited: list[str] = []
            for _ in range(100):
                journaled = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT entry_lite_json FROM sys_journal "
                        f"WHERE id = '{sent.invocation_id}' AND entry_type = 'Command: GetPromise'"
                    },
                )
                awaited = [
                    json.loads(row["entry_lite_json"])["Command"]["GetPromise"]["key"] for row in journaled.json()["rows"]
                ]
                if awaited:
                    break
                await asyncio.sleep(0.05)
            await admin.patch(f"/invocations/{sent.invocation_id}/kill")

            assert awaited == [relays.PICK_STORIES_PROMISE]
            assert steps == ["kept a job", "wrote stories for a job", "offered ['a story', 'another story']"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)

    async def test_a_run_its_key_does_not_name_ends_terminally_before_anything_is_kept(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        drafter_actions_service = restate.Service(f"DrafterActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        steps: list[str] = []
        fake_run_application_client = FakeRunApplicationClient(steps)
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateKeepRun(run_actions_service, fake_run_application_client),
            activities.RestateOfferStories(run_actions_service, fake_run_application_client),
            activities.RestateWriteStories(drafter_actions_service, FakeDrafterApplicationClient(steps)),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(
                    hypercorn_typing.ASGIFramework,
                    restate.app([run_actions_service, drafter_actions_service, run_orchestrator_workflow]),
                ),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            for _ in range(50):
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['STORY_DRAFTING_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_draft_stories.handler,
                        key="other-" + run_id,
                        arg=relays.DraftStoriesRequest(run_id=domain.RunId(run_id), job=domain.Job("a job")),
                    )

            assert foreign.value.status_code == 400
            assert steps == []
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
