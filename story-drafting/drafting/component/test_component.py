# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pathlib

import drafting.component as component


class TestConfig:

    def test_a_config_carries_the_engine_url(self) -> None:
        spec = component.Spec(
            engine_url="http://localhost:8080", identity_seed=7, sqlite_location="sqlite_location"
        )

        config = component.Config(spec)

        assert config.engine_url == spec.engine_url

    def test_a_config_carries_the_sqlite_location_its_store_is_built_with(self) -> None:
        spec = component.Spec(
            engine_url="http://localhost:8080", identity_seed=7, sqlite_location="sqlite_location"
        )

        config = component.Config(spec)

        assert config.sqlite_location == spec.sqlite_location

    def test_a_config_carries_the_seed_its_identity_repository_is_built_with(self) -> None:
        spec = component.Spec(
            engine_url="http://localhost:8080", identity_seed=7, sqlite_location="sqlite_location"
        )

        config = component.Config(spec)

        assert config.identity_seed == spec.identity_seed


class TestDrafting:

    async def test_the_component_publishes_the_engine_containers_it_registered_into(self, tmp_path: pathlib.Path) -> None:
        config = component.Config(
            component.Spec(
                engine_url="http://localhost:8080", identity_seed=7,
                sqlite_location=str(tmp_path / "sqlite_location")
            )
        )

        drafting = component.Drafting(config)
        registered = {
            drafting.story_actions_service.name: sorted(drafting.story_actions_service.handlers),
            drafting.jtbd_actions_service.name: sorted(drafting.jtbd_actions_service.handlers),
            drafting.jtbd_orchestrator_workflow.name: sorted(drafting.jtbd_orchestrator_workflow.handlers),
        }
        await drafting.close()

        assert registered == {
            "StoryActions": ["draft_stories"],
            "JtbdActions": ["record_stories"],
            "JtbdOrchestrator": ["story_drafting"],
        }

    async def test_every_container_bounds_its_retries_and_only_the_workflow_is_reachable_at_the_engine_url(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = component.Config(
            component.Spec(
                engine_url="http://localhost:8080", identity_seed=7,
                sqlite_location=str(tmp_path / "sqlite_location")
            )
        )

        drafting = component.Drafting(config)
        declared = [
            (
                registered.name,
                registered.ingress_private,
                registered.invocation_retry_policy.max_attempts if registered.invocation_retry_policy else None,
                registered.invocation_retry_policy.on_max_attempts if registered.invocation_retry_policy else None,
            )
            for registered in (
                drafting.story_actions_service,
                drafting.jtbd_actions_service,
                drafting.jtbd_orchestrator_workflow,
            )
        ]
        await drafting.close()

        assert declared == [
            ("StoryActions", True, 5, "pause"),
            ("JtbdActions", True, 5, "pause"),
            ("JtbdOrchestrator", None, 5, "pause"),
        ]
