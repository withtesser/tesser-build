from __future__ import annotations

import typing

import tesser.component as ts
import anthropic
import restate

import drafting.adapters.activities as activities
import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.gateways as gateways
import drafting.adapters.repositories as repositories
import drafting.adapters.workflows as workflows
import drafting.application as application
import drafting.client as client
import tesser.errors as errors

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, ingress: str, identity_seed: int, story_writing: str, anthropic_api_key: str) -> None:
        self.ingress = ingress
        self.identity_seed = identity_seed
        self.story_writing = story_writing
        self.anthropic_api_key = anthropic_api_key


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.identity_seed = spec.identity_seed
        self.story_writing = spec.story_writing
        self.anthropic_api_key = spec.anthropic_api_key


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        match config.story_writing:
            case "fixed":
                story_writing_actions = application.StoryWritingActions(gateways.FixedStoryWriting())
            case "anthropic":
                if not config.anthropic_api_key:
                    raise errors.invalid("missing_api_key", "drafting with anthropic needs an API key")
                story_writing_actions = application.StoryWritingActions(
                    gateways.AnthropicStoryWriting(anthropic.AsyncAnthropic(api_key=config.anthropic_api_key))
                )
            case "":
                raise errors.invalid("missing_coordinate", "the story writing coordinate is required")
            case _:
                raise errors.invalid("unknown_story_writing", f"story writing {config.story_writing!r} is not supported")
        self._memory_run_store = repositories.MemoryRunStore()
        self.run_actions_service: restate.Service = restate.Service(
            "RunActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.story_writing_actions_service: restate.Service = restate.Service(
            "StoryWritingActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_record_run = activities.RestateRecordRun(
            self.run_actions_service, application.RunActions(self._memory_run_store)
        )
        restate_write_stories = activities.RestateWriteStories(
            self.story_writing_actions_service, story_writing_actions
        )
        restate_draft_stories = workflows.RestateDraftStories(
            self.run_orchestrator_workflow, restate_record_run, restate_write_stories
        )
        self.client: client.DraftingClient = application.RunService(
            dispatchers.RestateHttpRunOrchestratorRelay(config.ingress, restate_draft_stories),
            repositories.UuidRunIdentityRepository(config.identity_seed),
            self._memory_run_store,
        )

    async def close(self) -> None:
        return None
