from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import jtbd.application as application
import jtbd.application.ports as ports
import jtbd.application.relays as relays
import jtbd.client as client


@ts.fake
class FakeJtbdOrchestratorRelay(relays.JtbdOrchestratorRelay):

    def __init__(self) -> None:
        self.conducted: list[relays.DraftForJtbdRequest] = []

    async def run_draft_for_jtbd(self, draft_for_jtbd_request: relays.DraftForJtbdRequest) -> relays.DraftForJtbdResponse:
        self.conducted.append(draft_for_jtbd_request)
        return relays.DraftForJtbdResponse(jtbd_id=draft_for_jtbd_request.jtbd_id)


@ts.fake
class FakeJtbdIdentityRepository(ports.JtbdIdentityRepository):

    async def issue_jtbd_id(self, issue_jtbd_id_request: ports.IssueJtbdIdRequest) -> ports.IssueJtbdIdResponse:
        return ports.IssueJtbdIdResponse(jtbd_id="jtbd-2")


@ts.fake
class FakeJtbdRepository(ports.JtbdRepository):

    def __init__(self, jbtds: dict[str, ports.Jtbd]) -> None:
        self._jbtds = jbtds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jbtds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            description=save_jtbd_request.description,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jbtds=(self._jbtds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jbtds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jbtds)


class TestJtbdService:

    async def test_submit_jtbd_conducts_the_jtbd_under_the_jtbd_id_its_identity_repository_issued(self) -> None:
        fake_jtbd_orchestrator_relay = FakeJtbdOrchestratorRelay()
        jtbd_service = application.JtbdService(
            fake_jtbd_orchestrator_relay, FakeJtbdIdentityRepository(), FakeJtbdStore()
        )

        submit_jtbd_response = await jtbd_service.submit_jtbd(
            client.SubmitJtbdRequest(description="design-feature", status="drafting")
        )

        assert [
            (conducted.jtbd_id, conducted.description, conducted.status)
            for conducted in fake_jtbd_orchestrator_relay.conducted
        ] == [("jtbd-2", "design-feature", "drafting")]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"

    async def test_a_saved_jtbd_is_read_back_by_its_jtbd_id(self) -> None:
        fake_jtbd_store = FakeJtbdStore()
        fake_jtbd_store.jbtds["jtbd-1"] = ports.Jtbd(
            jtbd_id="jtbd-1", description="design-feature", status="drafting"
        )
        jtbd_service = application.JtbdService(
            FakeJtbdOrchestratorRelay(), FakeJtbdIdentityRepository(), fake_jtbd_store
        )

        check_jtbd_status_response = await jtbd_service.check_jtbd_status(client.CheckJtbdStatusRequest(jtbd_id="jtbd-1"))

        assert check_jtbd_status_response.jtbd.jtbd_id == "jtbd-1"
        assert check_jtbd_status_response.jtbd.description == "design-feature"
        assert check_jtbd_status_response.jtbd.status == "drafting"
