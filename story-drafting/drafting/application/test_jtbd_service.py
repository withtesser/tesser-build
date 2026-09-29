from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeJtbdOrchestratorRelay(relays.JtbdOrchestratorRelay):

    def __init__(self) -> None:
        self.conducted: list[relays.ArrangeDraftingRequest] = []

    async def run_arrange_drafting(self, arrange_drafting_request: relays.ArrangeDraftingRequest) -> relays.ArrangeDraftingResponse:
        self.conducted.append(arrange_drafting_request)
        return relays.ArrangeDraftingResponse(jtbd_id=arrange_drafting_request.jtbd_id)


@ts.fake
class FakeJtbdIdentityRepository(ports.JtbdIdentityRepository):

    async def issue_jtbd_id(self, issue_jtbd_id_request: ports.IssueJtbdIdRequest) -> ports.IssueJtbdIdResponse:
        return ports.IssueJtbdIdResponse(jtbd_id="jtbd-2")


@ts.fake
class FakeJtbdRepository(ports.JtbdRepository):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbds=(self._jtbds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jtbds)


class TestJtbdService:

    async def test_submit_jtbd_conducts_the_jtbd_under_the_jtbd_id_its_identity_repository_issued(self) -> None:
        fake_jtbd_orchestrator_relay = FakeJtbdOrchestratorRelay()
        jtbd_service = application.JtbdService(
            fake_jtbd_orchestrator_relay, FakeJtbdIdentityRepository(), FakeJtbdStore()
        )

        submit_jtbd_response = await jtbd_service.submit_jtbd(
            client.SubmitJtbdRequest(status="pending")
        )

        assert [
            (conducted.jtbd_id, conducted.status)
            for conducted in fake_jtbd_orchestrator_relay.conducted
        ] == [("jtbd-2", "pending")]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"

    async def test_a_saved_jtbd_is_read_back_by_its_jtbd_id(self) -> None:
        fake_jtbd_store = FakeJtbdStore()
        fake_jtbd_store.jtbds["jtbd-1"] = ports.Jtbd(
            jtbd_id="jtbd-1", status="pending"
        )
        jtbd_service = application.JtbdService(
            FakeJtbdOrchestratorRelay(), FakeJtbdIdentityRepository(), fake_jtbd_store
        )

        check_jtbd_status_response = await jtbd_service.check_jtbd_status(client.CheckJtbdStatusRequest(jtbd_id="jtbd-1"))

        assert check_jtbd_status_response.jtbd.jtbd_id == "jtbd-1"
        assert check_jtbd_status_response.jtbd.status == "pending"
