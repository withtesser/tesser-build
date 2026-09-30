from __future__ import annotations

import tesser.testing as ts

import alpha.client as alpha_client
import alpha.component as alpha_component
import app as app
import beta.component as beta_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def __init__(self, storage: str) -> None:
        self._storage = storage

    def get(self) -> app.AppConfig:
        spec = app.Spec(alpha_component.Config(alpha_component.Spec(self._storage, "http://localhost:8080")), beta_component.Config(beta_component.Spec("a")))
        return app.AppConfig(spec)


class TestAppConfig:

    def test_a_config_carries_each_component_config(self) -> None:
        spec = app.Spec(alpha_component.Config(alpha_component.Spec("postgres://a@b/c", "http://localhost:8080")), beta_component.Config(beta_component.Spec("k")))
        app_config = app.AppConfig(spec)
        assert app_config.beta is spec.beta


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository(
            {"ALPHA_STORAGE": "postgres://a@b/c", "BETA_KEY": "k", "RESTATE_URL": "http://engine.invalid:8080"}
        ).get()
        assert (app_config.alpha.storage, app_config.beta.key, app_config.alpha.engine_url) == (
            "postgres://a@b/c",
            "k",
            "http://engine.invalid:8080",
        )


class TestApp:

    async def test_the_app_wires_alpha_through_beta(self, postgres_dsn: str) -> None:
        spec = app.Spec(alpha_component.Config(alpha_component.Spec(postgres_dsn, "http://localhost:8080")), beta_component.Config(beta_component.Spec("a")))
        minimal_app = app.MinimalApp(app.AppConfig(spec))
        add_part_response = await minimal_app.alpha.client.add_part(alpha_client.AddPartRequest(name="a", part="p"))
        assert add_part_response.name == "a"


class TestAppLoader:

    async def test_the_loader_builds_an_app_from_its_repository(self, postgres_dsn: str) -> None:
        app_loader = app.AppLoader(FakeConfigRepository(postgres_dsn))
        minimal_app = app_loader.load()
        add_part_response = await minimal_app.alpha.client.add_part(alpha_client.AddPartRequest(name="a", part="p"))
        assert add_part_response.name == "a"
