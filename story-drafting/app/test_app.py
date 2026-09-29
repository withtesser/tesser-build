from __future__ import annotations

import os

import tesser.testing as ts

import app
import jtbd.component as jtbd_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def get(self) -> app.AppConfig:
        ingress = os.environ["RESTATE_INGRESS"]
        return app.AppConfig(
            app.Spec(jtbd_component.Config(jtbd_component.Spec(ingress, 7)))
        )


class TestAppConfig:

    def test_a_config_carries_the_jtbd_config(self) -> None:
        spec = app.Spec(
            jtbd_component.Config(
                jtbd_component.Spec("http://localhost:8080", 7)
            )
        )

        app_config = app.AppConfig(spec)

        assert app_config.jtbd is spec.jtbd


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository().get()

        assert app_config.jtbd.ingress == os.environ["RESTATE_INGRESS"]

    def test_each_read_draws_a_new_identity_seed(self) -> None:
        env_config_repository = app.EnvConfigRepository()

        first = env_config_repository.get()
        second = env_config_repository.get()

        assert first.jtbd.identity_seed != second.jtbd.identity_seed


class TestAppLoader:

    def test_the_loader_builds_an_app_that_publishes_the_jtbd_client(self) -> None:
        story_drafting_app = app.AppLoader(FakeConfigRepository()).load()

        assert story_drafting_app.jtbd.client is not None
