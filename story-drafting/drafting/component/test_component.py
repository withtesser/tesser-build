from __future__ import annotations

import pytest
import tesser.testing as ts

import drafting.component as component
import tesser.errors as errors


@ts.helper
def drafting_spec(
    ingress: str = "http://localhost:8080", identity_seed: int = 7, story_writing: str = "fixed", anthropic_api_key: str = ""
) -> component.Spec:
    return component.Spec(
        ingress=ingress, identity_seed=identity_seed, story_writing=story_writing, anthropic_api_key=anthropic_api_key
    )


class TestConfig:

    def test_a_config_constructs_from_its_spec(self) -> None:
        spec = drafting_spec(story_writing="anthropic", anthropic_api_key="key")

        config = component.Config(spec)

        assert config.ingress == spec.ingress
        assert config.identity_seed == spec.identity_seed
        assert config.story_writing == spec.story_writing
        assert config.anthropic_api_key == spec.anthropic_api_key


class TestDrafting:

    async def test_the_component_publishes_the_engine_containers_it_registered_into(self) -> None:
        drafting = component.Drafting(component.Config(drafting_spec()))
        registered = {
            drafting.run_actions_service.name: sorted(drafting.run_actions_service.handlers),
            drafting.story_writing_actions_service.name: sorted(drafting.story_writing_actions_service.handlers),
            drafting.run_orchestrator_workflow.name: sorted(drafting.run_orchestrator_workflow.handlers),
        }
        await drafting.close()

        assert registered == {
            "RunActions": ["record_run"],
            "StoryWritingActions": ["write_stories"],
            "RunOrchestrator": ["draft_stories"],
        }

    async def test_every_container_bounds_its_retries_and_only_the_workflow_faces_the_ingress(self) -> None:
        drafting = component.Drafting(component.Config(drafting_spec()))
        declared = [
            (
                registered.name,
                registered.ingress_private,
                registered.invocation_retry_policy.max_attempts if registered.invocation_retry_policy else None,
                registered.invocation_retry_policy.on_max_attempts if registered.invocation_retry_policy else None,
            )
            for registered in (
                drafting.run_actions_service,
                drafting.story_writing_actions_service,
                drafting.run_orchestrator_workflow,
            )
        ]
        await drafting.close()

        assert declared == [
            ("RunActions", True, 5, "pause"),
            ("StoryWritingActions", True, 5, "pause"),
            ("RunOrchestrator", None, 5, "pause"),
        ]

    async def test_the_anthropic_coordinate_with_a_key_builds(self) -> None:
        drafting = component.Drafting(component.Config(drafting_spec(story_writing="anthropic", anthropic_api_key="key")))
        await drafting.close()

        assert drafting.story_writing_actions_service.name == "StoryWritingActions"

    def test_the_anthropic_coordinate_without_a_key_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(drafting_spec(story_writing="anthropic", anthropic_api_key="")))

    def test_an_absent_story_writing_coordinate_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(drafting_spec(story_writing="")))

    def test_an_unknown_story_writing_coordinate_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(drafting_spec(story_writing="guesswork")))
