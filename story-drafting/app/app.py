from __future__ import annotations

import os
import typing

import tesser.app as ts

import drafting.component as drafting_component
import tesser.errors as errors

_REQUIRED: typing.Final[tuple[str, ...]] = ("RESTATE_INGRESS", "STORY_DRAFTING_DRAFTER", "STORY_DRAFTING_STORAGE")


class Spec(ts.Spec):

    def __init__(self, drafting: drafting_component.Config) -> None:
        self.drafting = drafting


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.drafting = spec.drafting


class StoryDraftingApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.drafting = drafting_component.Drafting(app_config.drafting)

    async def close(self) -> None:
        await self.drafting.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        settings: dict[str, str] = {}
        for name in _REQUIRED:
            value = os.environ.get(name)
            if value is None:
                raise errors.invalid("missing_env", f"{name} is required")
            settings[name] = value
        return AppConfig(
            Spec(
                drafting=drafting_component.Config(
                    drafting_component.Spec(
                        ingress=settings["RESTATE_INGRESS"],
                        drafter=settings["STORY_DRAFTING_DRAFTER"],
                        storage=settings["STORY_DRAFTING_STORAGE"],
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
