from __future__ import annotations

import typing

import tesser.component as ts
import restate

import story_drafting.adapters.activities as activities
import story_drafting.adapters.dispatchers as dispatchers
import story_drafting.adapters.repositories as repositories
import story_drafting.adapters.workflows as workflows
import story_drafting.application as application
import story_drafting.client as client

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, ingress: str, identity_seed: int) -> None:
        self.ingress = ingress
        self.identity_seed = identity_seed


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.identity_seed = spec.identity_seed


class StoryDrafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_job_to_be_done_store = repositories.MemoryJobToBeDoneStore()
        self.job_to_be_done_actions_service: restate.Service = restate.Service(
            "JobToBeDoneActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.job_to_be_done_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JobToBeDoneOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_work_through_jtbd = workflows.RestateWorkThroughJtbd(
            self.job_to_be_done_orchestrator_workflow,
            activities.RestateRecordJtbd(
                self.job_to_be_done_actions_service, application.JobToBeDoneActions(self._memory_job_to_be_done_store)
            ),
        )
        self.client: client.StoryDraftingClient = application.JobToBeDoneService(
            dispatchers.RestateHttpJobToBeDoneOrchestratorRelay(config.ingress, restate_work_through_jtbd),
            repositories.UuidJobToBeDoneIdentityRepository(config.identity_seed),
            self._memory_job_to_be_done_store,
        )

    async def close(self) -> None:
        return None
