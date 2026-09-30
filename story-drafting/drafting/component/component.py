# pragma: tesser-generated; regenerate from the composition, never edit by hand
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

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(
        self, ingress: str, identity_seed: int, sqlite_location: str
    ) -> None:
        self.ingress = ingress
        self.identity_seed = identity_seed
        self.sqlite_location = sqlite_location


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.identity_seed = spec.identity_seed
        self.sqlite_location = spec.sqlite_location


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._sqlite_jtbd_repository = repositories.SqliteJtbdRepository(location=config.sqlite_location)
        self.story_actions_service: restate.Service = restate.Service(
            "StoryActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.jtbd_actions_service: restate.Service = restate.Service(
            "JtbdActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.jtbd_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JtbdOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_draft_jtbd_stories = workflows.RestateDraftJtbdStories(
            self.jtbd_orchestrator_workflow,
            activities.RestateDraftStories(
                self.story_actions_service,
                application.StoryActions(gateways.CannedStoryDrafter()),
            ),
            activities.RestateRecordStories(
                self.jtbd_actions_service,
                application.JtbdActions(self._sqlite_jtbd_repository),
            ),
        )
        self.client: client.DraftingClient = application.JtbdService(
            repositories.UuidJtbdIdentityRepository(config.identity_seed),
            self._sqlite_jtbd_repository,
            dispatchers.RestateHttpJtbdOrchestratorRelay(config.ingress, restate_draft_jtbd_stories),
        )

    async def close(self) -> None:
        return None
