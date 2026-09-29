from __future__ import annotations

import jtbds.adapters.repositories as repositories
import jtbds.application.ports as ports


class TestMemoryJobToBeDoneStore:

    async def test_a_saved_job_to_be_done_is_loaded_in_a_later_transaction(self) -> None:
        memory_job_to_be_done_store = repositories.MemoryJobToBeDoneStore()

        async with memory_job_to_be_done_store.transaction() as job_to_be_done_repository:
            save_jtbd_response = await job_to_be_done_repository.save_jtbd(
                ports.SaveJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
            )
        async with memory_job_to_be_done_store.transaction() as job_to_be_done_repository:
            load_jtbd_response = await job_to_be_done_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert save_jtbd_response == ports.SaveJtbdResponse(jtbd_id="jtbd-1")
        assert load_jtbd_response.jtbds == (
            ports.JobToBeDone(jtbd_id="jtbd-1", description="design new feature", status="drafting"),
        )

    async def test_a_job_to_be_done_never_saved_loads_nothing(self) -> None:
        memory_job_to_be_done_store = repositories.MemoryJobToBeDoneStore()

        async with memory_job_to_be_done_store.transaction() as job_to_be_done_repository:
            load_jtbd_response = await job_to_be_done_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert load_jtbd_response.jtbds == ()

    async def test_two_stores_hold_two_separate_jtbds(self) -> None:
        memory_job_to_be_done_store = repositories.MemoryJobToBeDoneStore()
        other_store = repositories.MemoryJobToBeDoneStore()

        async with memory_job_to_be_done_store.transaction() as job_to_be_done_repository:
            await job_to_be_done_repository.save_jtbd(
                ports.SaveJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
            )
        async with other_store.transaction() as job_to_be_done_repository:
            load_jtbd_response = await job_to_be_done_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert load_jtbd_response.jtbds == ()
