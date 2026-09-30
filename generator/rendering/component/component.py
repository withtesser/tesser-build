from __future__ import annotations

import tesser.component as ts

import rendering.adapters.repositories as repositories
import rendering.application as application
import rendering.client as client


class Spec(ts.Spec):

    def __init__(self, pieces_root: str) -> None:
        self.pieces_root = pieces_root


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.pieces_root = spec.pieces_root


class Rendering(ts.Component):

    def __init__(self, config: Config) -> None:
        self.client: client.RenderingClient = application.RenderingService(
            repositories.FilesystemCompositionReader(config.pieces_root),
            repositories.FilesystemRenderingWriter(),
        )

    def close(self) -> None:
        return None
