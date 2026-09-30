# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pathlib

import tesser.testing as ts

import app
import drafting.component as drafting_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def __init__(self, locations: pathlib.Path) -> None:
        self._locations = locations

    def get(self) -> app.AppConfig:
        return app.AppConfig(
            app.Spec(drafting_component.Config(drafting_component.Spec(
                "http://localhost:8080", 7, sqlite_location=str(self._locations / "sqlite_location")
            )))
        )


class TestAppConfig:

    def test_a_config_carries_the_drafting_config(self) -> None:
        spec = app.Spec(
            drafting_component.Config(
                drafting_component.Spec(
                    "http://localhost:8080", 7, sqlite_location="sqlite_location"
                )
            )
        )

        app_config = app.AppConfig(spec)

        assert app_config.drafting is spec.drafting


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository(
            {"RESTATE_URL": "http://engine.invalid:8080", "JTBD_DB_PATH": "sqlite_location.invalid"}
        ).get()

        assert app_config.drafting.engine_url == "http://engine.invalid:8080"
        assert app_config.drafting.sqlite_location == "sqlite_location.invalid"

    def test_each_read_draws_a_new_identity_seed(self) -> None:
        env_config_repository = app.EnvConfigRepository(
            {"RESTATE_URL": "http://engine.invalid:8080", "JTBD_DB_PATH": "sqlite_location.invalid"}
        )

        first = env_config_repository.get()
        second = env_config_repository.get()

        assert first.drafting.identity_seed != second.drafting.identity_seed


class TestAppLoader:

    def test_the_loader_builds_an_app_that_publishes_the_drafting_client(self, tmp_path: pathlib.Path) -> None:
        story_drafting_app = app.AppLoader(FakeConfigRepository(tmp_path)).load()

        assert story_drafting_app.drafting.client is not None
