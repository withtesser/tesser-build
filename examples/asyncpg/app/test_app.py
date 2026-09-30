from __future__ import annotations

import tesser.testing as ts

import alpha.client as alpha_client
import alpha.component as alpha_component
import app
import beta.client as beta_client
import beta.component as beta_component


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def __init__(self, storage_url: str) -> None:
        self._storage_url = storage_url

    def get(self) -> app.AppConfig:
        spec = app.Spec(
            alpha_component.Config(alpha_component.Spec(self._storage_url)),
            beta_component.Config(beta_component.Spec(self._storage_url)),
        )
        return app.AppConfig(spec)


class TestAppConfig:

    def test_a_config_carries_each_component_config(self) -> None:
        spec = app.Spec(
            alpha_component.Config(alpha_component.Spec("postgres://a@b/alpha")),
            beta_component.Config(beta_component.Spec("postgres://a@b/beta")),
        )
        app_config = app.AppConfig(spec)
        assert app_config.beta is spec.beta


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository(
            {"ALPHA_STORAGE": "postgres://a@b/alpha", "BETA_STORAGE": "postgres://a@b/beta"}
        ).get()
        assert app_config.alpha.storage == "postgres://a@b/alpha"
        assert app_config.beta.storage == "postgres://a@b/beta"


class TestApp:

    async def test_two_contexts_on_one_dsn_share_one_database_and_alpha_reaches_beta(self, storage_url: str) -> None:
        dsn = storage_url
        spec = app.Spec(
            alpha_component.Config(alpha_component.Spec(dsn)),
            beta_component.Config(beta_component.Spec(dsn)),
        )
        asyncpg_app = app.AsyncpgApp(app.AppConfig(spec))
        await asyncpg_app.open()
        await asyncpg_app.beta.client.hold_key(beta_client.HoldKeyRequest(key="shared"))
        add_part_response = await asyncpg_app.alpha.client.add_part(
            alpha_client.AddPartRequest(name="shared", part="p")
        )
        await asyncpg_app.close()
        assert add_part_response.name == "shared"
        assert len(asyncpg_app.databases) == 1

    async def test_two_dsns_give_two_databases(self) -> None:
        spec = app.Spec(
            alpha_component.Config(alpha_component.Spec("postgres://nobody@nowhere/alpha")),
            beta_component.Config(beta_component.Spec("postgres://nobody@nowhere/beta")),
        )
        asyncpg_app = app.AsyncpgApp(app.AppConfig(spec))
        await asyncpg_app.close()
        assert len(asyncpg_app.databases) == 2


class TestAppLoader:

    async def test_the_loader_builds_an_app_from_its_repository(self, storage_url: str) -> None:
        asyncpg_app = app.AppLoader(FakeConfigRepository(storage_url)).load()
        await asyncpg_app.open()
        add_part_response = await asyncpg_app.alpha.client.add_part(
            alpha_client.AddPartRequest(name="loader-a", part="p")
        )
        await asyncpg_app.close()
        assert add_part_response.name == "loader-a"
