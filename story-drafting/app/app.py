from __future__ import annotations

import os
import secrets
import typing

import tesser.app as ts

import jtbd.component as jtbd_component
import tesser.errors as errors

_IDENTITY_SEED_BITS: typing.Final[int] = 128


class Spec(ts.Spec):

    def __init__(self, jtbd: jtbd_component.Config) -> None:
        self.jtbd = jtbd


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.jtbd = spec.jtbd


class StoryDraftingApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.jtbd = jtbd_component.Jtbd(app_config.jtbd)

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        await self.jtbd.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        ingress = os.environ.get("RESTATE_INGRESS")
        if ingress is None:
            raise errors.invalid("missing_env", "RESTATE_INGRESS is required")
        return AppConfig(
            Spec(
                jtbd=jtbd_component.Config(
                    jtbd_component.Spec(
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
