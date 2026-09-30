from __future__ import annotations

import tesser.testing as ts

import app
import calls.client as calls_client
import calls.component as calls_component


@ts.helper
def calls_spec(
    storage: str = "postgres://a@b/calls",
    engine_url: str = "http://localhost:8080",
    livekit_url: str = "ws://livekit",
    livekit_api_key: str = "key",
    livekit_api_secret: str = "secret",
    livekit_agent_name: str = "caller",
) -> calls_component.Spec:
    return calls_component.Spec(
        storage=storage,
        engine_url=engine_url,
        livekit_url=livekit_url,
        livekit_api_key=livekit_api_key,
        livekit_api_secret=livekit_api_secret,
        livekit_agent_name=livekit_agent_name,
    )


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def __init__(self, storage: str, engine_url: str) -> None:
        self._storage = storage
        self._engine_url = engine_url

    def get(self) -> app.AppConfig:
        return app.AppConfig(
            app.Spec(calls_component.Config(calls_spec(storage=self._storage, engine_url=self._engine_url)))
        )


class TestAppConfig:

    def test_a_config_carries_the_calls_config(self) -> None:
        spec = app.Spec(calls_component.Config(calls_spec()))

        app_config = app.AppConfig(spec)

        assert app_config.calls is spec.calls


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        app_config = app.EnvConfigRepository(
            {
                "CALLS_STORAGE": "postgres://a@b/calls",
                "RESTATE_URL": "http://engine.invalid:8080",
                "LIVEKIT_URL": "ws://livekit.invalid",
                "LIVEKIT_API_KEY": "key",
                "LIVEKIT_API_SECRET": "secret",
                "LIVEKIT_AGENT_NAME": "caller",
            }
        ).get()

        assert app_config.calls.storage == "postgres://a@b/calls"
        assert app_config.calls.engine_url == "http://engine.invalid:8080"
        assert app_config.calls.livekit_url == "ws://livekit.invalid"
        assert app_config.calls.livekit_agent_name == "caller"


class TestAppLoader:

    async def test_the_loader_builds_an_app_whose_client_can_look_up_a_call(
        self, postgres_dsn: str, engine_url: str
    ) -> None:
        voice_app = app.AppLoader(FakeConfigRepository(postgres_dsn, engine_url)).load()
        await voice_app.open()

        raised: list[calls_client.CallNotFound] = []
        try:
            await voice_app.calls.client.get_call(calls_client.GetCallRequest(call_id="app-never-placed"))
        except calls_client.CallNotFound as call_not_found:
            raised.append(call_not_found)
        await voice_app.close()

        assert [str(call_not_found) for call_not_found in raised] == ["no call 'app-never-placed'"]
