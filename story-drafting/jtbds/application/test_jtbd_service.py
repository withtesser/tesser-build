from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import jtbds.application as application
import jtbds.application.ports as ports
import jtbds.application.relays as relays
import jtbds.client as client


@ts.fake
class FakeJtbdOrchestratorRelay(relays.JtbdOrchestratorRelay):

    def __init__(self) -> None:
        self.conducted: list[relays.WorkThroughJtbdRequest] = []

    async def start_work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.StartWorkThroughJtbdResponse:
        self.conducted.append(work_through_jtbd_request)
        return relays.StartWorkThroughJtbdResponse(jtbd_id=work_through_jtbd_request.jtbd_id)


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
            job=save_jtbd_request.job,
            step=save_jtbd_request.step,
            draft_count=save_jtbd_request.draft_count,
            picked_draft=save_jtbd_request.picked_draft,
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
            client.SubmitJtbdRequest(job="Design a login page, get my sign-off, then build it", step="drafting", draft_count=0, picked_draft="none")
        )

        assert [
            (conducted.jtbd_id, conducted.job, conducted.step, conducted.draft_count, conducted.picked_draft)
            for conducted in fake_jtbd_orchestrator_relay.conducted
        ] == [("jtbd-2", "Design a login page, get my sign-off, then build it", "drafting", 0, "none")]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"

    async def test_a_saved_jtbd_is_read_back_by_its_jtbd_id(self) -> None:
        fake_jtbd_store = FakeJtbdStore()
        fake_jtbd_store.jtbds["jtbd-1"] = ports.Jtbd(
            jtbd_id="jtbd-1", job="Design a login page, get my sign-off, then build it", step="drafting", draft_count=0, picked_draft="none"
        )
        jtbd_service = application.JtbdService(
            FakeJtbdOrchestratorRelay(), FakeJtbdIdentityRepository(), fake_jtbd_store
        )

        get_jtbd_response = await jtbd_service.get_jtbd(client.GetJtbdRequest(jtbd_id="jtbd-1"))

        assert get_jtbd_response.jtbd.jtbd_id == "jtbd-1"
        assert get_jtbd_response.jtbd.job == "Design a login page, get my sign-off, then build it"
        assert get_jtbd_response.jtbd.step == "drafting"
        assert get_jtbd_response.jtbd.draft_count == 0
        assert get_jtbd_response.jtbd.picked_draft == "none"
