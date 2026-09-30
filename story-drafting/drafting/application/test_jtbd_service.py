# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeJtbdIdentityRepository(ports.JtbdIdentityRepository):

    def __init__(self) -> None:
        self.issue_jtbd_id_requests: list[ports.IssueJtbdIdRequest] = []

    async def issue_jtbd_id(self, issue_jtbd_id_request: ports.IssueJtbdIdRequest) -> ports.IssueJtbdIdResponse:
        self.issue_jtbd_id_requests.append(issue_jtbd_id_request)
        return ports.IssueJtbdIdResponse(jtbd_id="jtbd-2")


@ts.fake
class FakeJtbdRepository(ports.JtbdRepository):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd.jtbd_id] = save_jtbd_request.jtbd
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbd=self._jtbds[load_jtbd_request.jtbd_id])


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jtbds)


@ts.fake
class FakeJtbdOrchestratorRelay(relays.JtbdOrchestratorRelay):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds
        self.saved_when_received: list[bool] = []
        self.received: list[relays.StoryDraftingRequest] = []

    async def start_story_drafting(self, story_drafting_request: relays.StoryDraftingRequest) -> relays.StartStoryDraftingResponse:
        self.received.append(story_drafting_request)
        self.saved_when_received.append(story_drafting_request.jtbd_id in self._jtbds)
        return relays.StartStoryDraftingResponse(jtbd_id=story_drafting_request.jtbd_id)


class TestJtbdService:

    async def test_submit_jtbd_start_story_drafting_with_the_jtbd_it_built(self) -> None:
        fake_jtbd_identity_repository = FakeJtbdIdentityRepository()
        fake_jtbd_store = FakeJtbdStore()
        fake_jtbd_orchestrator_relay = FakeJtbdOrchestratorRelay(fake_jtbd_store.jtbds)
        jtbd_service = application.JtbdService(fake_jtbd_identity_repository, fake_jtbd_store, fake_jtbd_orchestrator_relay)

        submit_jtbd_response = await jtbd_service.submit_jtbd(client.SubmitJtbdRequest(role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep"))

        assert [(received.jtbd_id, received.role, received.i_want, received.so_that,) for received in fake_jtbd_orchestrator_relay.received] == [("jtbd-2", "a developer", "stories drafted for my job to be done", "I can decide which to keep",)]
        assert fake_jtbd_orchestrator_relay.saved_when_received == [True]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"
        assert submit_jtbd_response.status in ("drafting_stories", "awaiting_story_acceptance")

    async def test_get_jtbd_answers_the_jtbd_it_loads(self) -> None:
        fake_jtbd_identity_repository = FakeJtbdIdentityRepository()
        fake_jtbd_store = FakeJtbdStore()
        fake_jtbd_orchestrator_relay = FakeJtbdOrchestratorRelay(fake_jtbd_store.jtbds)
        fake_jtbd_store.jtbds["jtbd-1"] = ports.Jtbd(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep", stories=(ports.Story(given="a job to be done", when="I submit it", then="it is drafting its stories", state="drafted"),))
        jtbd_service = application.JtbdService(fake_jtbd_identity_repository, fake_jtbd_store, fake_jtbd_orchestrator_relay)

        get_jtbd_response = await jtbd_service.get_jtbd(client.GetJtbdRequest(jtbd_id="jtbd-1"))

        assert get_jtbd_response.jtbd_id == "jtbd-1"
        assert get_jtbd_response.status in ("drafting_stories", "awaiting_story_acceptance")
        assert get_jtbd_response.stories == (client.Story(given="a job to be done", when="I submit it", then="it is drafting its stories", state="drafted"),)
