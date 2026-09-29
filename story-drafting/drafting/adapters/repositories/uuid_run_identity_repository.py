from __future__ import annotations

import random
import uuid

import tesser.adapters as ts

import drafting.application.ports as ports


class UuidRunIdentityRepository(ts.Repository):

    def __init__(self, seed: int) -> None:
        self._random = random.Random(seed)

    async def issue_run_id(self, issue_run_id_request: ports.IssueRunIdRequest) -> ports.IssueRunIdResponse:
        return ports.IssueRunIdResponse(run_id=str(uuid.UUID(int=self._random.getrandbits(128), version=4)))
