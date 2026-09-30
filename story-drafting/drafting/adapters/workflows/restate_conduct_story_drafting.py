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


class RestateConductStoryDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.ConductStoryDraftingRequest]):

    def serialize(self, conduct_story_drafting_request: relays.ConductStoryDraftingRequest | None) -> bytes:
        if conduct_story_drafting_request is None:
            return b""
        return relays.ConductStoryDraftingRequestSnapshot().serialize(conduct_story_drafting_request)

    def deserialize(self, buf: bytes) -> relays.ConductStoryDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductStoryDraftingRequestSnapshot().deserialize(buf)


class RestateConductStoryDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.ConductStoryDraftingResponse]):

    def serialize(self, conduct_story_drafting_response: relays.ConductStoryDraftingResponse | None) -> bytes:
        if conduct_story_drafting_response is None:
            return b""
        return relays.ConductStoryDraftingResponseSnapshot().serialize(conduct_story_drafting_response)

    def deserialize(self, buf: bytes) -> relays.ConductStoryDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductStoryDraftingResponseSnapshot().deserialize(buf)


class RestateInvocationDrafterActionsRelay(ts.Dispatcher):

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


class RestateInvocationJtbdOrchestratorSignalRelay(ts.Dispatcher):

    def __init__(
        self,
        restate_workflow_context: restate.WorkflowContext,
    ) -> None:
        self._restate_workflow_context = restate_workflow_context

    async def await_accept_stories(self, await_accept_stories_request: relays.AwaitAcceptStoriesRequest) -> relays.AwaitAcceptStoriesResponse:
        return relays.AwaitAcceptStoriesResponseSnapshot().deserialize(
            await self._restate_workflow_context.promise(relays.ACCEPT_STORIES_PROMISE, serde=restate_serde.BytesSerde()).value()
        )


class RestateConductStoryDrafting(ts.Workflow):

    def __init__(
        self,
        jtbd_orchestrator_workflow: restate.Workflow,
        restate_draft_stories: activities.RestateDraftStories,
        restate_record_stories: activities.RestateRecordStories,
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateConductStoryDraftingRequestSerde(),
            output_serde=RestateConductStoryDraftingResponseSerde(),
        )
        async def conduct_story_drafting(
            restate_workflow_context: restate.WorkflowContext, conduct_story_drafting_request: relays.ConductStoryDraftingRequest
        ) -> relays.ConductStoryDraftingResponse:
            if conduct_story_drafting_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationDrafterActionsRelay(restate_workflow_context, restate_draft_stories),
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_record_stories),
                RestateInvocationJtbdOrchestratorSignalRelay(restate_workflow_context),
            ).conduct_story_drafting(conduct_story_drafting_request)

        self.handler = conduct_story_drafting
