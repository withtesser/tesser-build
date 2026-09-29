from __future__ import annotations

import typing

import tesser.context as ts


class GenerateTreeRequest(ts.Request):

    def __init__(self, spec_path: str, out_dir: str, printed: tuple[str, ...]) -> None:
        self.spec_path = spec_path
        self.out_dir = out_dir
        self.printed = printed


class PrintedFile(ts.Response):

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class GenerateTreeResponse(ts.Response):

    def __init__(self, problems: tuple[str, ...], paths: tuple[str, ...], printed: tuple[PrintedFile, ...]) -> None:
        self.problems = problems
        self.paths = paths
        self.printed = printed


class TreesClient(ts.Client, typing.Protocol):

    def generate_tree(self, generate_tree_request: GenerateTreeRequest) -> GenerateTreeResponse: ...
