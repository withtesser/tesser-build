# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(self, submit_jtbd_request: client.SubmitJtbdRequest, issue_jtbd_id_response: ports.IssueJtbdIdResponse) -> None:
        super().__init__(
            jtbd_id=issue_jtbd_id_response.jtbd_id,
            role=submit_jtbd_request.role,
            i_want=submit_jtbd_request.i_want,
            so_that=submit_jtbd_request.so_that,
            stories=(),
        )


class MapToJtbd(ts.Mapper, ports.Jtbd):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
            role=str(jtbd.role),
            i_want=str(jtbd.i_want),
            so_that=str(jtbd.so_that),
            stories=tuple(ports.StorySpec(given=str(story.given), when=str(story.when), then=str(story.then), state=str(story.state)) for story in jtbd.stories),
        )


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd=MapToJtbd(jtbd),
        )


class MapToConductStoryDraftingRequest(ts.Mapper, relays.ConductStoryDraftingRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
            role=str(jtbd.role),
            i_want=str(jtbd.i_want),
            so_that=str(jtbd.so_that),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, jtbd: domain.Jtbd, start_conduct_story_drafting_response: relays.StartConductStoryDraftingResponse) -> None:
        super().__init__(
            jtbd_id=start_conduct_story_drafting_response.jtbd_id,
            status=str(jtbd.status),
        )


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, get_jtbd_request: client.GetJtbdRequest) -> None:
        super().__init__(
            jtbd_id=get_jtbd_request.jtbd_id,
        )


class MapToJtbdSpecWhenLoaded(ts.Mapper, domain.JtbdSpec):

    def __init__(self, load_jtbd_response: ports.LoadJtbdResponse) -> None:
        super().__init__(
            jtbd_id=load_jtbd_response.jtbd.jtbd_id,
            role=load_jtbd_response.jtbd.role,
            i_want=load_jtbd_response.jtbd.i_want,
            so_that=load_jtbd_response.jtbd.so_that,
            stories=tuple(domain.StorySpec(given=story.given, when=story.when, then=story.then, state=domain.StoryState(story.state)) for story in load_jtbd_response.jtbd.stories),
        )


class MapToGetJtbdResponse(ts.Mapper, client.GetJtbdResponse):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
            role=str(jtbd.role),
            i_want=str(jtbd.i_want),
            so_that=str(jtbd.so_that),
            status=str(jtbd.status),
            stories=tuple(client.StoryView(given=str(story.given), when=str(story.when), then=str(story.then), state=str(story.state)) for story in jtbd.stories),
        )


class JtbdService(ts.ApplicationService):

    def __init__(
        self,
        jtbd_identity_repository: ports.JtbdIdentityRepository,
        jtbd_store: ports.JtbdStore,
        jtbd_orchestrator_relay: relays.JtbdOrchestratorRelay,
    ) -> None:
        self._jtbd_identity_repository = jtbd_identity_repository
        self._jtbd_store = jtbd_store
        self._jtbd_orchestrator_relay = jtbd_orchestrator_relay

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        issue_jtbd_id_response = await self._jtbd_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())
        jtbd = domain.Jtbd(MapToJtbdSpec(submit_jtbd_request, issue_jtbd_id_response))
        async with self._jtbd_store.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(jtbd))
        start_conduct_story_drafting_response = await self._jtbd_orchestrator_relay.start_conduct_story_drafting(MapToConductStoryDraftingRequest(jtbd))
        return MapToSubmitJtbdResponse(jtbd, start_conduct_story_drafting_response)

    async def get_jtbd(self, get_jtbd_request: client.GetJtbdRequest) -> client.GetJtbdResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(MapToLoadJtbdRequest(get_jtbd_request))
        jtbd = domain.Jtbd(MapToJtbdSpecWhenLoaded(load_jtbd_response))
        return MapToGetJtbdResponse(jtbd)
