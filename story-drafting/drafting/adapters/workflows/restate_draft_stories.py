from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.adapters.activities as activities
import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the jtbd its workflow is keyed by"


class RestateDraftStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesRequest]):

    def serialize(self, draft_stories_request: relays.DraftStoriesRequest | None) -> bytes:
        if draft_stories_request is None:
            return b""
        return relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesRequestSnapshot().deserialize(buf)


class RestateDraftStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesResponse]):

    def serialize(self, draft_stories_response: relays.DraftStoriesResponse | None) -> bytes:
        if draft_stories_response is None:
            return b""
        return relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_write_drafts: activities.RestateWriteDrafts
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_write_drafts = restate_write_drafts

    async def run_write_drafts(self, write_drafts_request: relays.WriteDraftsRequest) -> relays.WriteDraftsResponse:
        return await self._restate_workflow_context.service_call(self._restate_write_drafts.handler, write_drafts_request)


class RestateDraftStories(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_write_drafts: activities.RestateWriteDrafts
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateDraftStoriesRequestSerde(),
            output_serde=RestateDraftStoriesResponseSerde(),
        )
        async def draft_stories(
            restate_workflow_context: restate.WorkflowContext, draft_stories_request: relays.DraftStoriesRequest
        ) -> relays.DraftStoriesResponse:
            if draft_stories_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_write_drafts)
            ).draft_stories(draft_stories_request)

        self.handler = draft_stories
