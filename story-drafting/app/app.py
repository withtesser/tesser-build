from __future__ import annotations

import os
import typing

import tesser.app as ts

import drafting.component as drafting_component
import tesser.errors as errors


class Spec(ts.Spec):

    def __init__(self, drafting: drafting_component.Config) -> None:
        self.drafting = drafting


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.drafting = spec.drafting


class StoryDraftingApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.drafting = drafting_component.Drafting(app_config.drafting)

    def close(self) -> None:
        self.drafting.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        engine_url = os.environ.get("RESTATE_URL")
        if engine_url is None:
            raise errors.invalid("missing_env", "RESTATE_URL is required")
        story_writer = os.environ.get("STORY_WRITER")
        if story_writer is None:
            raise errors.invalid("missing_env", "STORY_WRITER is required")
        return AppConfig(
            Spec(
                drafting=drafting_component.Config(
                    drafting_component.Spec(
                        engine_url=engine_url,
                        story_writer=story_writer,
                        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
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
