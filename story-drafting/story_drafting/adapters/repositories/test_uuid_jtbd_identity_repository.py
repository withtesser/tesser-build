from __future__ import annotations

import uuid

import story_drafting.adapters.repositories as repositories
import story_drafting.application.ports as ports


class TestUuidJtbdIdentityRepository:

    async def test_the_same_seed_issues_the_same_jtbd_id(self) -> None:
        uuid_jtbd_identity_repository = repositories.UuidJtbdIdentityRepository(7)
        same_seed = repositories.UuidJtbdIdentityRepository(7)

        first = await uuid_jtbd_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())
        second = await same_seed.issue_jtbd_id(ports.IssueJtbdIdRequest())

        assert first.jtbd_id == second.jtbd_id

    async def test_each_jtbd_id_issued_is_a_different_version_4_uuid(self) -> None:
        uuid_jtbd_identity_repository = repositories.UuidJtbdIdentityRepository(7)

        first = await uuid_jtbd_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())
        second = await uuid_jtbd_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())

        assert first.jtbd_id != second.jtbd_id
        assert uuid.UUID(first.jtbd_id).version == 4
