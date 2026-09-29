from __future__ import annotations

import enum
import typing

import tesser.application as ts


class DocumentState(enum.Enum):
    READ = "read"
    MISSING = "missing"
    UNREADABLE = "unreadable"


class TargetState(enum.Enum):
    ABSENT = "absent"
    OCCUPIED = "occupied"
    NOT_DIRECTORY = "not_directory"


class DocumentRecord(ts.Response):

    def __init__(self, name: str, state: DocumentState, text: str) -> None:
        self.name = name
        self.state = state
        self.text = text


class PieceRecord(ts.Response):

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class ExistingFileRecord(ts.Response):

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class TargetRecord(ts.Response):

    def __init__(self, state: TargetState, files: tuple[ExistingFileRecord, ...]) -> None:
        self.state = state
        self.files = files


class ReadCompositionRequest(ts.Request):

    def __init__(self, composition_dir: str, out_dir: str) -> None:
        self.composition_dir = composition_dir
        self.out_dir = out_dir


class ReadCompositionResponse(ts.Response):

    def __init__(
        self, documents: tuple[DocumentRecord, ...], pieces: tuple[PieceRecord, ...], target: TargetRecord
    ) -> None:
        self.documents = documents
        self.pieces = pieces
        self.target = target


class CompositionReader(ts.Port, typing.Protocol):

    def read_composition(self, read_composition_request: ReadCompositionRequest) -> ReadCompositionResponse: ...
