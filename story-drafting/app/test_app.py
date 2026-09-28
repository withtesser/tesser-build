from __future__ import annotations

import os
import tempfile

import pytest

import tesser.testing as ts

import app as app
import drafting.client as drafting_client
import drafting.component as drafting_component
import tesser.errors as errors


@ts.fake
class FakeConfigRepository(app.AppConfigRepository):

    def __init__(self, storage: str) -> None:
        self._storage = storage

    def get(self) -> app.AppConfig:
        spec = app.Spec(drafting_component.Config(drafting_component.Spec(self._storage, "http://127.0.0.1:9")))
        return app.AppConfig(spec)


class TestAppConfig:

    def test_a_config_carries_each_component_config(self) -> None:
        spec = app.Spec(drafting_component.Config(drafting_component.Spec("/tmp/runs", "http://127.0.0.1:9")))
        app_config = app.AppConfig(spec)

        assert app_config.drafting is spec.drafting


class TestEnvConfigRepository:

    def test_the_environment_is_read_into_a_config(self) -> None:
        ambient = {name: os.environ.get(name) for name in ("STORY_DRAFTING_STORAGE", "RESTATE_INGRESS")}
        os.environ.update(STORY_DRAFTING_STORAGE="/tmp/runs", RESTATE_INGRESS="http://ingress.invalid:8080")
        try:
            app_config = app.EnvConfigRepository().get()
        finally:
            for name, value in ambient.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        assert (app_config.drafting.storage, app_config.drafting.ingress) == (
            "/tmp/runs",
            "http://ingress.invalid:8080",
        )

    def test_a_missing_storage_is_refused(self) -> None:
        ambient = os.environ.pop("STORY_DRAFTING_STORAGE", None)
        try:
            with pytest.raises(errors.DomainError):
                app.EnvConfigRepository().get()
        finally:
            if ambient is not None:
                os.environ["STORY_DRAFTING_STORAGE"] = ambient


class TestAppLoader:

    async def test_the_loader_builds_an_app_from_its_repository(self) -> None:
        with tempfile.TemporaryDirectory() as storage:
            story_drafting_app = app.AppLoader(FakeConfigRepository(storage)).load()
            try:
                with pytest.raises(drafting_client.RunNotFound):
                    await story_drafting_app.drafting.client.get_run(drafting_client.GetRunRequest(run_id="never"))
            finally:
                story_drafting_app.close()
