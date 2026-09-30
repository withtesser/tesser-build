# pragma: tesser-generated; regenerate from the composition, never edit by hand
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


class RestateDraftJtbdStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdStoriesRequest]):

    def serialize(self, draft_jtbd_stories_request: relays.DraftJtbdStoriesRequest | None) -> bytes:
        if draft_jtbd_stories_request is None:
            return b""
        return relays.DraftJtbdStoriesRequestSnapshot().serialize(draft_jtbd_stories_request)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdStoriesRequestSnapshot().deserialize(buf)


class RestateDraftJtbdStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdStoriesResponse]):

    def serialize(self, draft_jtbd_stories_response: relays.DraftJtbdStoriesResponse | None) -> bytes:
        if draft_jtbd_stories_response is None:
            return b""
        return relays.DraftJtbdStoriesResponseSnapshot().serialize(draft_jtbd_stories_response)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdStoriesResponseSnapshot().deserialize(buf)


class RestateInvocationStoryActionsRelay(ts.Dispatcher):

    def __init__(
        self,
        restate_workflow_context: restate.WorkflowContext,
        restate_draft_stories: activities.RestateDraftStories,
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_draft_stories = restate_draft_stories

    async def run_draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        return await self._restate_workflow_context.service_call(self._restate_draft_stories.handler, draft_stories_request)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self,
        restate_workflow_context: restate.WorkflowContext,
        restate_record_stories: activities.RestateRecordStories,
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_record_stories = restate_record_stories

    async def run_record_stories(self, record_stories_request: relays.RecordStoriesRequest) -> relays.RecordStoriesResponse:
        return await self._restate_workflow_context.service_call(self._restate_record_stories.handler, record_stories_request)


class RestateDraftJtbdStories(ts.Workflow):

    def __init__(
        self,
        jtbd_orchestrator_workflow: restate.Workflow,
        restate_draft_stories: activities.RestateDraftStories,
        restate_record_stories: activities.RestateRecordStories,
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateDraftJtbdStoriesRequestSerde(),
            output_serde=RestateDraftJtbdStoriesResponseSerde(),
        )
        async def draft_jtbd_stories(
            restate_workflow_context: restate.WorkflowContext, draft_jtbd_stories_request: relays.DraftJtbdStoriesRequest
        ) -> relays.DraftJtbdStoriesResponse:
            if draft_jtbd_stories_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationStoryActionsRelay(restate_workflow_context, restate_draft_stories),
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_record_stories),
            ).draft_jtbd_stories(draft_jtbd_stories_request)

        self.handler = draft_jtbd_stories
