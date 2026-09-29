from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import jtbds.application as application
import jtbds.application.ports as ports
import jtbds.application.relays as relays


@ts.fake
class FakeJobToBeDoneRepository(ports.JobToBeDoneRepository):

    def __init__(self, jtbds: dict[str, ports.JobToBeDone]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd_id] = ports.JobToBeDone(
            jtbd_id=save_jtbd_request.jtbd_id,
            description=save_jtbd_request.description,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbds=(self._jtbds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJobToBeDoneStore(ports.JobToBeDoneStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.JobToBeDone] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JobToBeDoneRepository]:
        yield FakeJobToBeDoneRepository(self.jtbds)


class TestJobToBeDoneActions:

    async def test_initialize_jtbd_saves_the_job_to_be_done_under_its_jtbd_id(self) -> None:
        fake_job_to_be_done_store = FakeJobToBeDoneStore()
        job_to_be_done_actions = application.JobToBeDoneActions(fake_job_to_be_done_store)

        await job_to_be_done_actions.initialize_jtbd(
            relays.InitializeJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
        )

        assert fake_job_to_be_done_store.jtbds["jtbd-1"] == ports.JobToBeDone(
            jtbd_id="jtbd-1", description="design new feature", status="drafting"
        )

    async def test_initialize_jtbd_answers_the_jtbd_id_it_saved(self) -> None:
        job_to_be_done_actions = application.JobToBeDoneActions(FakeJobToBeDoneStore())

        initialize_jtbd_response = await job_to_be_done_actions.initialize_jtbd(
            relays.InitializeJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
        )

        assert initialize_jtbd_response.jtbd_id == "jtbd-1"
