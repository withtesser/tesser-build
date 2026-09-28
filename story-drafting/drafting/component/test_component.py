from __future__ import annotations

import pytest

import drafting.component as component
import tesser.errors as errors


class TestConfig:

    def test_a_config_carries_its_spec(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", story_writer="anthropic", anthropic_api_key="key")
        config = component.Config(spec)
        assert (config.ingress, config.story_writer, config.anthropic_api_key) == (
            spec.ingress,
            spec.story_writer,
            spec.anthropic_api_key,
        )


class TestDrafting:

    def test_only_the_workflow_faces_the_ingress_and_each_container_holds_its_handlers(self) -> None:
        drafting = component.Drafting(
            component.Config(component.Spec(ingress="http://localhost:8080", story_writer="canned", anthropic_api_key=""))
        )
        try:
            declared = [
                (registered.name, registered.ingress_private, sorted(registered.handlers))
                for registered in (
                    drafting.run_actions_service,
                    drafting.story_actions_service,
                    drafting.run_orchestrator_workflow,
                )
            ]
        finally:
            drafting.close()
        assert declared == [
            ("RunActions", True, ["record_run"]),
            ("StoryActions", True, ["write_stories"]),
            ("RunOrchestrator", None, ["draft_stories"]),
        ]

    def test_the_anthropic_coordinate_builds_with_a_key(self) -> None:
        drafting = component.Drafting(
            component.Config(
                component.Spec(ingress="http://localhost:8080", story_writer="anthropic", anthropic_api_key="key")
            )
        )
        drafting.close()
        assert sorted(drafting.story_actions_service.handlers) == ["write_stories"]

    def test_an_absent_story_writer_coordinate_is_refused_by_name(self) -> None:
        with pytest.raises(errors.DomainError) as caught:
            component.Drafting(
                component.Config(component.Spec(ingress="http://localhost:8080", story_writer="", anthropic_api_key=""))
            )
        assert caught.value.code == "missing_coordinate"

    def test_an_unknown_story_writer_is_refused_by_name(self) -> None:
        with pytest.raises(errors.DomainError) as caught:
            component.Drafting(
                component.Config(component.Spec(ingress="http://localhost:8080", story_writer="gpt", anthropic_api_key=""))
            )
        assert caught.value.code == "unknown_story_writer"
        assert "gpt" in caught.value.message

    def test_the_anthropic_story_writer_without_a_key_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as caught:
            component.Drafting(
                component.Config(
                    component.Spec(ingress="http://localhost:8080", story_writer="anthropic", anthropic_api_key="")
                )
            )
        assert caught.value.code == "missing_api_key"
