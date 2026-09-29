from __future__ import annotations

import uuid

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestUuidRunIdentityRepository:

    async def test_the_same_seed_issues_the_same_run_id(self) -> None:
        uuid_run_identity_repository = repositories.UuidRunIdentityRepository(7)
        same_seed = repositories.UuidRunIdentityRepository(7)

        first = await uuid_run_identity_repository.issue_run_id(ports.IssueRunIdRequest())
        second = await same_seed.issue_run_id(ports.IssueRunIdRequest())

        assert first.run_id == second.run_id

    async def test_each_run_id_issued_is_a_different_version_4_uuid(self) -> None:
        uuid_run_identity_repository = repositories.UuidRunIdentityRepository(7)

        first = await uuid_run_identity_repository.issue_run_id(ports.IssueRunIdRequest())
        second = await uuid_run_identity_repository.issue_run_id(ports.IssueRunIdRequest())

        assert first.run_id != second.run_id
        assert uuid.UUID(first.run_id).version == 4
