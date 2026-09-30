from __future__ import annotations

import pathlib

import tesser.adapters as ts

import rendering.application.ports as ports


class FilesystemRenderingWriter(ts.Repository):

    def write_rendering(self, write_rendering_request: ports.WriteRenderingRequest) -> ports.WriteRenderingResponse:
        root = pathlib.Path(write_rendering_request.out_dir).resolve()
        refused = tuple(
            file_record.path
            for file_record in write_rendering_request.files
            if not (root / file_record.path).resolve().is_relative_to(root)
        )
        if refused:
            return ports.WriteRenderingResponse(paths=(), refused=refused)
        for file_record in write_rendering_request.files:
            written = root / file_record.path
            written.parent.mkdir(parents=True, exist_ok=True)
            written.write_text(file_record.text, encoding="utf-8")
        return ports.WriteRenderingResponse(
            paths=tuple(file_record.path for file_record in write_rendering_request.files), refused=()
        )
