# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import collections.abc as collections_abc
import os
import secrets
import typing

import tesser.app as ts

import drafting.component as drafting_component
import tesser.errors as errors

_IDENTITY_SEED_BITS: typing.Final[int] = 128


class Spec(ts.Spec):

    def __init__(self, drafting: drafting_component.Config) -> None:
        self.drafting = drafting


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.drafting = spec.drafting


class StoryDraftingApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.drafting = drafting_component.Drafting(app_config.drafting)

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        await self.drafting.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def __init__(self, environ: collections_abc.Mapping[str, str]) -> None:
        self._environ = environ

    def get(self) -> AppConfig:
        engine_url = self._environ.get("RESTATE_URL")
        if engine_url is None:
            raise errors.invalid("missing_env", "RESTATE_URL is required")
        sqlite_location = self._environ.get("JTBD_DB_PATH")
        if sqlite_location is None:
            raise errors.invalid("missing_env", "JTBD_DB_PATH is required")
        return AppConfig(
            Spec(
                drafting=drafting_component.Config(
                    drafting_component.Spec(
                        engine_url=engine_url,
                        identity_seed=secrets.randbits(_IDENTITY_SEED_BITS),
                        sqlite_location=sqlite_location,
                    )
                )
            )
        )


class AppLoader(ts.Loader):

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        self._app_config_repository = app_config_repository

    def load(self) -> StoryDraftingApp:
        return StoryDraftingApp(self._app_config_repository.get())


@ts.load
def load() -> StoryDraftingApp:
    return AppLoader(EnvConfigRepository(os.environ)).load()
