from __future__ import annotations

import os

import tesser.testing as ts

import app
import drafting.component as drafting_component


@ts.helper
def drafting_spec(ingress: str = "http://localhost:8080", drafter: str = "deterministic") -> drafting_component.Spec:
    return drafting_component.Spec(ingress=ingress, drafter=drafter)


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def get(self) -> app.AppConfig:
        return app.AppConfig(app.Spec(drafting_component.Config(drafting_spec())))


class TestAppConfig:

    def test_a_config_carries_the_drafting_config(self) -> None:
        spec = app.Spec(drafting_component.Config(drafting_spec()))

        app_config = app.AppConfig(spec)

        assert app_config.drafting is spec.drafting


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository().get()

        assert app_config.drafting.ingress == os.environ["RESTATE_INGRESS"]
        assert app_config.drafting.drafter == os.environ["STORY_DRAFTING_DRAFTER"]


class TestAppLoader:

    async def test_the_loader_builds_an_app_that_publishes_the_drafting_client(self) -> None:
        story_drafting_app = app.AppLoader(FakeConfigRepository()).load()
        await story_drafting_app.close()

        assert hasattr(story_drafting_app.drafting.client, "draft_stories")
