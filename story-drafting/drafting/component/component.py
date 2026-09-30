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
_CANNED: typing.Final[str] = "canned"
_ANTHROPIC: typing.Final[str] = "anthropic"


class Spec(ts.Spec):

    def __init__(self, engine_url: str, story_writer: str, anthropic_api_key: str) -> None:
        self.engine_url = engine_url
        self.story_writer = story_writer
        self.anthropic_api_key = anthropic_api_key


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.engine_url = spec.engine_url
        self.story_writer = spec.story_writer
        self.anthropic_api_key = spec.anthropic_api_key


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        if not config.story_writer:
            raise errors.invalid("missing_coordinate", "the drafting story writer coordinate is required")
        if config.story_writer == _CANNED:
            story_actions = application.StoryActions(gateways.CannedStoryWriter())
        elif config.story_writer == _ANTHROPIC:
            if not config.anthropic_api_key:
                raise errors.invalid("missing_api_key", "the anthropic story writer needs an API key")
            story_actions = application.StoryActions(
                gateways.AnthropicStoryWriter(anthropic.AsyncAnthropic(api_key=config.anthropic_api_key))
            )
        else:
            raise errors.invalid("unknown_story_writer", f"story writer {config.story_writer!r} not supported")
        self._memory_run_store = repositories.MemoryRunStore()
        self.run_actions_service: restate.Service = restate.Service(
            "RunActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.story_actions_service: restate.Service = restate.Service(
            "StoryActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_draft_stories = workflows.RestateDraftStories(
            self.run_orchestrator_workflow,
            activities.RestateRecordRun(self.run_actions_service, application.RunActions(self._memory_run_store)),
            activities.RestateWriteStories(self.story_actions_service, story_actions),
        )
        self.client: client.DraftingClient = application.DraftingService(
            self._memory_run_store,
            dispatchers.RestateHttpRunOrchestratorRelay(config.engine_url, restate_draft_stories),
        )

    def close(self) -> None:
        return None
