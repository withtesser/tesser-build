from __future__ import annotations

import os
import secrets
import typing

import tesser.app as ts

import jtbds.component as jtbds_component
import tesser.errors as errors

_IDENTITY_SEED_BITS: typing.Final[int] = 128


class Spec(ts.Spec):

    def __init__(self, jtbds: jtbds_component.Config) -> None:
        self.jtbds = jtbds


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.jtbds = spec.jtbds


class StoryDraftingApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.jtbds = jtbds_component.Jtbds(app_config.jtbds)

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        await self.jtbds.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        ingress = os.environ.get("RESTATE_INGRESS")
        if ingress is None:
            raise errors.invalid("missing_env", "RESTATE_INGRESS is required")
        return AppConfig(
            Spec(
                jtbds=jtbds_component.Config(
                    jtbds_component.Spec(
                        ingress=ingress,
                        identity_seed=secrets.randbits(_IDENTITY_SEED_BITS),
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
    return AppLoader(EnvConfigRepository()).load()
