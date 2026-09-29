from __future__ import annotations

import os
import secrets
import typing

import tesser.app as ts

import story_drafting.component as story_drafting_component
import tesser.errors as errors

_IDENTITY_SEED_BITS: typing.Final[int] = 128


class Spec(ts.Spec):

    def __init__(self, story_drafting: story_drafting_component.Config) -> None:
        self.story_drafting = story_drafting


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.story_drafting = spec.story_drafting


class StoryDraftingSkillApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.story_drafting = story_drafting_component.StoryDrafting(app_config.story_drafting)

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        await self.story_drafting.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        ingress = os.environ.get("RESTATE_INGRESS")
        if ingress is None:
            raise errors.invalid("missing_env", "RESTATE_INGRESS is required")
        return AppConfig(
            Spec(
                story_drafting=story_drafting_component.Config(
                    story_drafting_component.Spec(
                        ingress=ingress,
                        identity_seed=secrets.randbits(_IDENTITY_SEED_BITS),
                    )
                )
            )
        )


class AppLoader(ts.Loader):

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        self._app_config_repository = app_config_repository

    def load(self) -> StoryDraftingSkillApp:
        return StoryDraftingSkillApp(self._app_config_repository.get())


@ts.load
def load() -> StoryDraftingSkillApp:
    return AppLoader(EnvConfigRepository()).load()
