from __future__ import annotations

import os

import tesser.testing as ts

import app
import jtbds.component as jtbds_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def get(self) -> app.AppConfig:
        ingress = os.environ["RESTATE_INGRESS"]
        return app.AppConfig(
            app.Spec(jtbds_component.Config(jtbds_component.Spec(ingress, 7)))
        )


class TestAppConfig:

    def test_a_config_carries_the_jtbds_config(self) -> None:
        spec = app.Spec(
            jtbds_component.Config(
                jtbds_component.Spec("http://localhost:8080", 7)
            )
        )

        app_config = app.AppConfig(spec)

        assert app_config.jtbds is spec.jtbds


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository().get()

        assert app_config.jtbds.ingress == os.environ["RESTATE_INGRESS"]

    def test_each_read_draws_a_new_identity_seed(self) -> None:
        env_config_repository = app.EnvConfigRepository()

        first = env_config_repository.get()
        second = env_config_repository.get()

        assert first.jtbds.identity_seed != second.jtbds.identity_seed


class TestAppLoader:

    def test_the_loader_builds_an_app_that_publishes_the_jtbds_client(self) -> None:
        story_drafting_app = app.AppLoader(FakeConfigRepository()).load()

        assert story_drafting_app.jtbds.client is not None
