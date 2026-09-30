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


class RestateStoryDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.StoryDraftingRequest]):

    def serialize(self, story_drafting_request: relays.StoryDraftingRequest | None) -> bytes:
        if story_drafting_request is None:
            return b""
        return relays.StoryDraftingRequestSnapshot().serialize(story_drafting_request)

    def deserialize(self, buf: bytes) -> relays.StoryDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.StoryDraftingRequestSnapshot().deserialize(buf)


class RestateStoryDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.StoryDraftingResponse]):

    def serialize(self, story_drafting_response: relays.StoryDraftingResponse | None) -> bytes:
        if story_drafting_response is None:
            return b""
        return relays.StoryDraftingResponseSnapshot().serialize(story_drafting_response)

    def deserialize(self, buf: bytes) -> relays.StoryDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.StoryDraftingResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self,
        restate_workflow_context: restate.WorkflowContext,
        restate_draft_stories: activities.RestateDraftStories,
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_draft_stories = restate_draft_stories

    async def run_draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        return await self._restate_workflow_context.service_call(self._restate_draft_stories.handler, draft_stories_request)


class RestateStoryDrafting(ts.Workflow):

    def __init__(
        self,
        jtbd_orchestrator_workflow: restate.Workflow,
        restate_draft_stories: activities.RestateDraftStories,
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateStoryDraftingRequestSerde(),
            output_serde=RestateStoryDraftingResponseSerde(),
        )
        async def story_drafting(
            restate_workflow_context: restate.WorkflowContext, story_drafting_request: relays.StoryDraftingRequest
        ) -> relays.StoryDraftingResponse:
            if story_drafting_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_draft_stories),
            ).story_drafting(story_drafting_request)

        self.handler = story_drafting
