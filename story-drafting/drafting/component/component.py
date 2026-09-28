from __future__ import annotations

import typing

import tesser.component as ts
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
_ANTHROPIC_API: typing.Final[str] = "https://api.anthropic.com"


class Spec(ts.Spec):

    def __init__(self, ingress: str, drafter: str, anthropic_api_key: str) -> None:
        self.ingress = ingress
        self.drafter = drafter
        self.anthropic_api_key = anthropic_api_key


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.drafter = spec.drafter
        self.anthropic_api_key = spec.anthropic_api_key


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        if config.drafter == "canned":
            drafter_actions = application.DrafterActions(gateways.CannedStoryDrafter())
        elif config.drafter == "anthropic":
            if not config.anthropic_api_key:
                raise errors.invalid("missing_api_key", "the anthropic drafter needs an Anthropic API key")
            drafter_actions = application.DrafterActions(
                gateways.AnthropicStoryDrafter(config.anthropic_api_key, _ANTHROPIC_API)
            )
        else:
            raise errors.invalid("unknown_drafter", f"drafter {config.drafter!r} not supported")
        self._memory_run_repository = repositories.MemoryRunRepository()
        self.run_actions_service: restate.Service = restate.Service(
            "RunActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.drafter_actions_service: restate.Service = restate.Service(
            "DrafterActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        run_actions = application.RunActions(self._memory_run_repository)
        restate_draft_stories = workflows.RestateDraftStories(
            self.run_orchestrator_workflow,
            activities.RestateKeepRun(self.run_actions_service, run_actions),
            activities.RestateOfferStories(self.run_actions_service, run_actions),
            activities.RestateWriteStories(self.drafter_actions_service, drafter_actions),
        )
        self.client: client.DraftingClient = application.RunService(
            self._memory_run_repository,
            dispatchers.RestateHttpRunOrchestratorRelay(config.ingress, restate_draft_stories),
        )

    def close(self) -> None:
        self._memory_run_repository.close()
