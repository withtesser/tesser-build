from __future__ import annotations

import tempfile

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestFileRunStore:

    async def test_a_run_saved_in_one_transaction_is_loaded_in_the_next(self) -> None:
        with tempfile.TemporaryDirectory() as storage:
            file_run_store = repositories.FileRunStore(storage)
            async with file_run_store.transaction() as run_repository:
                issue_run_id_response = await run_repository.issue_run_id(ports.IssueRunIdRequest())
                missing = await run_repository.load_run(ports.LoadRunRequest(run_id=issue_run_id_response.run_id))
                await run_repository.save_run(
                    ports.SaveRunRequest(
                        run_id=issue_run_id_response.run_id,
                        job="ship a release",
                        step="drafting",
                        drafted_stories=("a story",),
                        accepted_stories=(),
                    )
                )
            async with file_run_store.transaction() as run_repository:
                found = await run_repository.load_run(ports.LoadRunRequest(run_id=issue_run_id_response.run_id))

        assert (missing.outcome, missing.runs) == (ports.LoadRunOutcome.NOT_FOUND, ())
        assert found.outcome == ports.LoadRunOutcome.FOUND
        assert found.runs == (
            ports.Run(
                run_id=issue_run_id_response.run_id,
                job="ship a release",
                step="drafting",
                drafted_stories=("a story",),
                accepted_stories=(),
            ),
        )

    async def test_each_issued_run_id_is_new(self) -> None:
        with tempfile.TemporaryDirectory() as storage:
            async with repositories.FileRunStore(storage).transaction() as run_repository:
                first = await run_repository.issue_run_id(ports.IssueRunIdRequest())
                second = await run_repository.issue_run_id(ports.IssueRunIdRequest())

        assert first.run_id != second.run_id
