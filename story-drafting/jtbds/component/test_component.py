from __future__ import annotations

import jtbds.component as component


class TestConfig:

    def test_a_config_carries_the_engine_ingress(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", identity_seed=7)

        config = component.Config(spec)

        assert config.ingress == spec.ingress

    def test_a_config_carries_the_seed_its_identity_repository_is_built_with(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", identity_seed=7)

        config = component.Config(spec)

        assert config.identity_seed == spec.identity_seed


class TestJtbds:

    async def test_the_component_publishes_the_engine_containers_it_registered_into(self) -> None:
        config = component.Config(
            component.Spec(ingress="http://localhost:8080", identity_seed=7)
        )

        jtbds = component.Jtbds(config)
        registered = {
            jtbds.job_to_be_done_actions_service.name: sorted(jtbds.job_to_be_done_actions_service.handlers),
            jtbds.job_to_be_done_orchestrator_workflow.name: sorted(
                jtbds.job_to_be_done_orchestrator_workflow.handlers
            ),
        }
        await jtbds.close()

        assert registered == {"JobToBeDoneActions": ["initialize_jtbd"], "JobToBeDoneOrchestrator": ["process_jtbd"]}

    async def test_every_container_bounds_its_retries_and_only_the_workflow_faces_the_ingress(self) -> None:
        config = component.Config(
            component.Spec(ingress="http://localhost:8080", identity_seed=7)
        )

        jtbds = component.Jtbds(config)
        declared = [
            (
                registered.name,
                registered.ingress_private,
                registered.invocation_retry_policy.max_attempts if registered.invocation_retry_policy else None,
                registered.invocation_retry_policy.on_max_attempts if registered.invocation_retry_policy else None,
            )
            for registered in (jtbds.job_to_be_done_actions_service, jtbds.job_to_be_done_orchestrator_workflow)
        ]
        await jtbds.close()

        assert declared == [
            ("JobToBeDoneActions", True, 5, "pause"),
            ("JobToBeDoneOrchestrator", None, 5, "pause"),
        ]
