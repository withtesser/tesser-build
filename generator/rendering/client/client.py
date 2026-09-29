from __future__ import annotations

import typing

import tesser.context as ts


class RenderCompositionRequest(ts.Request):

    def __init__(self, composition_dir: str, out_dir: str) -> None:
        self.composition_dir = composition_dir
        self.out_dir = out_dir


class RenderCompositionResponse(ts.Response):

    def __init__(self, problems: tuple[str, ...], written: tuple[str, ...], kept: tuple[str, ...]) -> None:
        self.problems = problems
        self.written = written
        self.kept = kept


class RenderingClient(ts.Client, typing.Protocol):

    def render_composition(self, render_composition_request: RenderCompositionRequest) -> RenderCompositionResponse: ...
