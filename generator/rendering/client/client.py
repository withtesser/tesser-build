from __future__ import annotations

import typing

import tesser.context as ts


class RenderCompositionRequest(ts.Request):

    def __init__(self, composition_dir: str, out_dir: str, printed: tuple[str, ...]) -> None:
        self.composition_dir = composition_dir
        self.out_dir = out_dir
        self.printed = printed


class PrintedFile(ts.Response):

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class RenderCompositionResponse(ts.Response):

    def __init__(
        self,
        problems: tuple[str, ...],
        written: tuple[str, ...],
        removed: tuple[str, ...],
        kept: tuple[str, ...],
        printed: tuple[PrintedFile, ...],
    ) -> None:
        self.problems = problems
        self.written = written
        self.removed = removed
        self.kept = kept
        self.printed = printed


class CheckCompositionRequest(ts.Request):

    def __init__(self, composition_dir: str, tree_dir: str) -> None:
        self.composition_dir = composition_dir
        self.tree_dir = tree_dir


class CheckCompositionResponse(ts.Response):

    def __init__(self, problems: tuple[str, ...], drifted: tuple[str, ...], checked: int) -> None:
        self.problems = problems
        self.drifted = drifted
        self.checked = checked


class RenderingClient(ts.Client, typing.Protocol):

    def render_composition(self, render_composition_request: RenderCompositionRequest) -> RenderCompositionResponse: ...

    def check_composition(self, check_composition_request: CheckCompositionRequest) -> CheckCompositionResponse: ...
