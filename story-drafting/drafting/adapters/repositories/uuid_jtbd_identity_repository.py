from __future__ import annotations

import random
import uuid

import tesser.adapters as ts

import drafting.application.ports as ports


class UuidJtbdIdentityRepository(ts.Repository):

    def __init__(self, seed: int) -> None:
        self._random = random.Random(seed)

    async def issue_jtbd_id(self, issue_jtbd_id_request: ports.IssueJtbdIdRequest) -> ports.IssueJtbdIdResponse:
        return ports.IssueJtbdIdResponse(jtbd_id=str(uuid.UUID(int=self._random.getrandbits(128), version=4)))
