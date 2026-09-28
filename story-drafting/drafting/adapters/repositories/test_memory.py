from __future__ import annotations

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestMemoryRunStore:

    async def test_a_saved_run_is_loaded_back_in_a_later_transaction(self) -> None:
        memory_run_store = repositories.MemoryRunStore()

        async with memory_run_store.transaction() as run_repository:
            save_run_response = await run_repository.save_run(
                ports.SaveRunRequest(run_id="run-1", job="plan a migration", stage="drafting")
            )
        async with memory_run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="run-1"))

        assert save_run_response.run_id == "run-1"
        assert load_run_response.runs == (ports.Run(run_id="run-1", job="plan a migration", stage="drafting"),)

    async def test_saving_a_run_again_keeps_one_run_under_its_run_id(self) -> None:
        memory_run_store = repositories.MemoryRunStore()

        async with memory_run_store.transaction() as run_repository:
            await run_repository.save_run(ports.SaveRunRequest(run_id="run-1", job="plan a migration", stage="drafting"))
            await run_repository.save_run(ports.SaveRunRequest(run_id="run-1", job="plan a migration", stage="drafting"))
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="run-1"))

        assert len(load_run_response.runs) == 1

    async def test_a_run_never_saved_loads_as_no_run(self) -> None:
        async with repositories.MemoryRunStore().transaction() as run_repository:
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="run-9"))

        assert load_run_response.runs == ()
