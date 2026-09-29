from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def record_submission(self, record_submission_request: relays.RecordSubmissionRequest) -> relays.RecordSubmissionResponse: ...
