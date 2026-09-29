from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import jtbds.application.client as client
import jtbds.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateRecordSubmissionRequestSerde(ts.Serde, restate_serde.Serde[relays.RecordSubmissionRequest]):

    def serialize(self, record_submission_request: relays.RecordSubmissionRequest | None) -> bytes:
        if record_submission_request is None:
            return b""
        return relays.RecordSubmissionRequestSnapshot().serialize(record_submission_request)

    def deserialize(self, buf: bytes) -> relays.RecordSubmissionRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordSubmissionRequestSnapshot().deserialize(buf)


class RestateRecordSubmissionResponseSerde(ts.Serde, restate_serde.Serde[relays.RecordSubmissionResponse]):

    def serialize(self, record_submission_response: relays.RecordSubmissionResponse | None) -> bytes:
        if record_submission_response is None:
            return b""
        return relays.RecordSubmissionResponseSnapshot().serialize(record_submission_response)

    def deserialize(self, buf: bytes) -> relays.RecordSubmissionResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordSubmissionResponseSnapshot().deserialize(buf)


class RestateRecordSubmission(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateRecordSubmissionRequestSerde(),
            output_serde=RestateRecordSubmissionResponseSerde(),
        )
        async def record_submission(
            restate_context: restate.Context, record_submission_request: relays.RecordSubmissionRequest
        ) -> relays.RecordSubmissionResponse:
            return await jtbd_application_client.record_submission(record_submission_request)

        self.handler = record_submission
