from __future__ import annotations

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestMemoryRunStore:

    async def test_a_saved_run_is_loaded_back_in_a_later_transaction(self) -> None:
        memory_run_store = repositories.MemoryRunStore()
        async with memory_run_store.transaction() as run_repository:
            save_run_response = await run_repository.save_run(
                ports.SaveRunRequest(run_id="r1", job="ship", stage="awaiting_pick", stories=("a story",), accepted_stories=())
            )
        async with memory_run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="r1"))
        assert save_run_response == ports.SaveRunResponse(run_id="r1")
        assert load_run_response == ports.LoadRunResponse(
            outcome=ports.LoadRunOutcome.FOUND,
            runs=(ports.RunRecord(run_id="r1", job="ship", stage="awaiting_pick", stories=("a story",), accepted_stories=()),),
        )

    async def test_saving_a_run_again_replaces_it(self) -> None:
        memory_run_store = repositories.MemoryRunStore()
        async with memory_run_store.transaction() as run_repository:
            await run_repository.save_run(
                ports.SaveRunRequest(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=())
            )
            await run_repository.save_run(
                ports.SaveRunRequest(run_id="r1", job="ship", stage="awaiting_pick", stories=("a",), accepted_stories=())
            )
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="r1"))
        assert [run_record.stage for run_record in load_run_response.runs] == ["awaiting_pick"]

    async def test_a_run_never_saved_is_not_found(self) -> None:
        async with repositories.MemoryRunStore().transaction() as run_repository:
            load_run_response = await run_repository.load_run(ports.LoadRunRequest(run_id="r1"))
        assert load_run_response == ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())
