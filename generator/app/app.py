from __future__ import annotations

import pathlib
import typing

import tesser.app as ts

import rendering.component as rendering_component
import trees.component as trees_component

TEMPLATES: typing.Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[1] / "templates"

PIECES: typing.Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[1] / "pieces"


class Spec(ts.Spec):

    def __init__(self, trees: trees_component.Config, rendering: rendering_component.Config) -> None:
        self.trees = trees
        self.rendering = rendering


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.trees = spec.trees
        self.rendering = spec.rendering


class GeneratorApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        self.trees = trees_component.Trees(app_config.trees)
        self.rendering = rendering_component.Rendering(app_config.rendering)

    def close(self) -> None:
        self.trees.close()
        self.rendering.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def get(self) -> AppConfig:
        return AppConfig(
            Spec(
                trees=trees_component.Config(trees_component.Spec(templates_root=str(TEMPLATES))),
                rendering=rendering_component.Config(rendering_component.Spec(pieces_root=str(PIECES))),
            )
        )


class AppLoader(ts.Loader):

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        self._app_config_repository = app_config_repository

    def load(self) -> GeneratorApp:
        return GeneratorApp(self._app_config_repository.get())


@ts.load
def load() -> GeneratorApp:
    return AppLoader(EnvConfigRepository()).load()
