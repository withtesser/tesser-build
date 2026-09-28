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

DETERMINISTIC: typing.Final[str] = "deterministic"
ANTHROPIC: typing.Final[str] = "anthropic"
_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, storage: str, ingress: str, drafter: str, anthropic_api_key: str) -> None:
        self.storage = storage
        self.ingress = ingress
        self.drafter = drafter
        self.anthropic_api_key = anthropic_api_key


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.storage = spec.storage
        self.ingress = spec.ingress
        self.drafter = spec.drafter
        self.anthropic_api_key = spec.anthropic_api_key


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        if config.drafter == DETERMINISTIC:
            drafting_actions = application.DraftingActions(gateways.DeterministicStoryDrafter())
        elif config.drafter == ANTHROPIC:
            if not config.anthropic_api_key:
                raise errors.invalid("missing_coordinate", "the anthropic drafter needs an API key")
            drafting_actions = application.DraftingActions(
                gateways.AnthropicStoryDrafter(anthropic.AsyncAnthropic(api_key=config.anthropic_api_key))
            )
        else:
            raise errors.invalid("unknown_drafter", f"drafter {config.drafter!r} is not supported")
        self._file_run_store = repositories.FileRunStore(config.storage)
        self.drafting_actions_service: restate.Service = restate.Service(
            "DraftingActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_actions_service: restate.Service = restate.Service(
            "RunActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_draft_stories = activities.RestateDraftStories(self.drafting_actions_service, drafting_actions)
        restate_record_run = activities.RestateRecordRun(
            self.run_actions_service, application.RunActions(self._file_run_store)
        )
        restate_conduct_run = workflows.RestateConductRun(
            self.run_orchestrator_workflow, restate_draft_stories, restate_record_run
        )
        self.client: client.DraftingClient = application.RunService(
            self._file_run_store,
            dispatchers.RestateHttpRunOrchestratorRelay(config.ingress, restate_conduct_run),
        )

    def close(self) -> None:
        return None
