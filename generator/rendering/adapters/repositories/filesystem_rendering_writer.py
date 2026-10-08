from __future__ import annotations

import pathlib
import shutil

import tesser.adapters as ts

import rendering.application.ports as ports


class FilesystemRenderingWriter(ts.Repository):

    def write_rendering(self, write_rendering_request: ports.WriteRenderingRequest) -> ports.WriteRenderingResponse:
        root = pathlib.Path(write_rendering_request.out_dir).resolve()
        refused = tuple(
            path
            for path in [file_record.path for file_record in write_rendering_request.files] + list(write_rendering_request.removed)
            if not (root / path).resolve().is_relative_to(root)
        )
        if refused:
            return ports.WriteRenderingResponse(paths=(), removed=(), refused=refused)
        for file_record in write_rendering_request.files:
            written = root / file_record.path
            written.parent.mkdir(parents=True, exist_ok=True)
            written.write_text(file_record.text, encoding="utf-8")
        removed: list[str] = []
        for path in write_rendering_request.removed:
            gone = root / path
            if not gone.is_file():
                continue
            gone.unlink()
            removed.append(path)
            directory = gone.parent
            while directory != root and directory.is_dir() and all(entry.name == "__pycache__" for entry in directory.iterdir()):
                for cache in directory.iterdir():
                    shutil.rmtree(cache)
                directory.rmdir()
                directory = directory.parent
        return ports.WriteRenderingResponse(
            paths=tuple(file_record.path for file_record in write_rendering_request.files), removed=tuple(removed), refused=()
        )
