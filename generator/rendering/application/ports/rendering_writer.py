from __future__ import annotations

import typing

import tesser.application as ts


class FileRecord(ts.Request):

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class WriteRenderingRequest(ts.Request):

    def __init__(self, out_dir: str, files: tuple[FileRecord, ...], removed: tuple[str, ...]) -> None:
        self.out_dir = out_dir
        self.files = files
        self.removed = removed


class WriteRenderingResponse(ts.Response):

    def __init__(self, paths: tuple[str, ...], removed: tuple[str, ...], refused: tuple[str, ...]) -> None:
        self.paths = paths
        self.removed = removed
        self.refused = refused


class RenderingWriter(ts.Port, typing.Protocol):

    def write_rendering(self, write_rendering_request: WriteRenderingRequest) -> WriteRenderingResponse: ...
