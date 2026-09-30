from __future__ import annotations

import pathlib
import typing

import tesser.adapters as ts

import rendering.application.ports as ports

PIECE_SUFFIX: typing.Final[str] = ".tmpl"

DOCUMENTS: typing.Final[tuple[str, ...]] = ("language", "story", "composition", "implementations", "generator")


class FilesystemCompositionReader(ts.Repository):

    def __init__(self, pieces_root: str) -> None:
        self._pieces_root = pieces_root

    def read_composition(self, read_composition_request: ports.ReadCompositionRequest) -> ports.ReadCompositionResponse:
        composition_dir = pathlib.Path(read_composition_request.composition_dir)
        documents: list[ports.DocumentRecord] = []
        for name in DOCUMENTS:
            document_path = composition_dir / f"{name}.toml"
            try:
                text = document_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                documents.append(ports.DocumentRecord(name=name, state=ports.DocumentState.MISSING, text=""))
            except (OSError, UnicodeDecodeError):
                documents.append(ports.DocumentRecord(name=name, state=ports.DocumentState.UNREADABLE, text=""))
            else:
                documents.append(ports.DocumentRecord(name=name, state=ports.DocumentState.READ, text=text))
        out_dir = pathlib.Path(read_composition_request.out_dir)
        existing: tuple[ports.ExistingFileRecord, ...] = ()
        if not out_dir.exists():
            state = ports.TargetState.ABSENT
        elif not out_dir.is_dir():
            state = ports.TargetState.NOT_DIRECTORY
        else:
            state = ports.TargetState.OCCUPIED
            existing = tuple(
                ports.ExistingFileRecord(
                    path=found_path.relative_to(out_dir).as_posix(),
                    text=found_path.read_bytes().decode("utf-8", errors="replace"),
                )
                for found_path in sorted(out_dir.rglob("*"))
                if found_path.is_file() and "__pycache__" not in found_path.parts
            )
        pieces_root = pathlib.Path(self._pieces_root)
        found = sorted(pieces_root.rglob(f"*{PIECE_SUFFIX}")) if pieces_root.is_dir() else []
        return ports.ReadCompositionResponse(
            documents=tuple(documents),
            pieces=tuple(
                ports.PieceRecord(path=piece_path.relative_to(pieces_root).as_posix(), text=piece_path.read_text(encoding="utf-8"))
                for piece_path in found
                if piece_path.is_file()
            ),
            target=ports.TargetRecord(state=state, files=existing),
        )
