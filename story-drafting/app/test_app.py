from __future__ import annotations

import tesser.testing as ts

import app as app
import drafting.component as drafting_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def get(self) -> app.AppConfig:
        spec = app.Spec(drafting_component.Config(drafting_component.Spec("http://localhost:8080", "canned", "")))
        return app.AppConfig(spec)


class TestAppConfig:

    def test_a_config_carries_the_component_config(self) -> None:
        spec = app.Spec(drafting_component.Config(drafting_component.Spec("http://localhost:8080", "canned", "")))
        app_config = app.AppConfig(spec)
        assert app_config.drafting is spec.drafting


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository({"RESTATE_URL": "http://engine.invalid:8080", "STORY_WRITER": "canned"}).get()
        assert (app_config.drafting.engine_url, app_config.drafting.story_writer) == ("http://engine.invalid:8080", "canned")


class TestStoryDraftingApp:

    def test_the_app_wires_drafting(self) -> None:
        spec = app.Spec(drafting_component.Config(drafting_component.Spec("http://localhost:8080", "canned", "")))
        story_drafting_app = app.StoryDraftingApp(app.AppConfig(spec))
        try:
            declared = [
                story_drafting_app.drafting.run_actions_service.name,
                story_drafting_app.drafting.story_actions_service.name,
                story_drafting_app.drafting.run_orchestrator_workflow.name,
            ]
        finally:
            story_drafting_app.close()
        assert declared == ["RunActions", "StoryActions", "RunOrchestrator"]


class TestAppLoader:

    def test_the_loader_builds_an_app_from_its_repository(self) -> None:
        story_drafting_app = app.AppLoader(FakeConfigRepository()).load()
        try:
            declared = [
                sorted(story_drafting_app.drafting.run_actions_service.handlers),
                sorted(story_drafting_app.drafting.story_actions_service.handlers),
                sorted(story_drafting_app.drafting.run_orchestrator_workflow.handlers),
            ]
        finally:
            story_drafting_app.close()
        assert declared == [["record_run"], ["write_stories"], ["draft_stories"]]
