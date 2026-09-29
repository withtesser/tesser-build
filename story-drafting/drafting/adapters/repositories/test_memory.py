from __future__ import annotations

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestMemoryRunStore:

    async def test_a_saved_run_is_loaded_in_a_later_transaction(self) -> None:
        memory_run_store = repositories.MemoryRunStore()

        async with memory_run_store.transaction() as run_repository:
            save_run_response = await run_repository.save_run(
                ports.SaveRunRequest(run_id="run-1", job="Plan a trip")
            )
        async with memory_run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(
                ports.LoadRunRequest(run_id="run-1")
            )

        assert save_run_response == ports.SaveRunResponse(run_id="run-1")
        assert load_run_response.runs == (
            ports.Run(run_id="run-1", job="Plan a trip"),
        )

    async def test_a_run_never_saved_loads_nothing(self) -> None:
        memory_run_store = repositories.MemoryRunStore()

        async with memory_run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(
                ports.LoadRunRequest(run_id="run-1")
            )

        assert load_run_response.runs == ()

    async def test_two_stores_hold_two_separate_runs(self) -> None:
        memory_run_store = repositories.MemoryRunStore()
        other_store = repositories.MemoryRunStore()

        async with memory_run_store.transaction() as run_repository:
            await run_repository.save_run(
                ports.SaveRunRequest(run_id="run-1", job="Plan a trip")
            )
        async with other_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(
                ports.LoadRunRequest(run_id="run-1")
            )

        assert load_run_response.runs == ()
