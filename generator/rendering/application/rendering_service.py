from __future__ import annotations

import typing

import tesser.application as ts

import rendering.application.ports as ports
import rendering.client as client
import rendering.domain as domain


class MapToReadCompositionRequest(ts.Mapper, ports.ReadCompositionRequest):

    def __init__(self, render_composition_request: client.RenderCompositionRequest) -> None:
        super().__init__(
            composition_dir=render_composition_request.composition_dir,
            out_dir=render_composition_request.out_dir,
        )


class MapToRenderedTreeSpec(ts.Mapper, domain.RenderedTreeSpec):

    def __init__(
        self, read_composition_response: ports.ReadCompositionResponse, render_composition_request: client.RenderCompositionRequest
    ) -> None:
        super().__init__(
            documents=tuple(
                (document_record.name, document_record.state.value, document_record.text)
                for document_record in read_composition_response.documents
            ),
            pieces=tuple((piece_record.path, piece_record.text) for piece_record in read_composition_response.pieces),
            target=read_composition_response.target.state.value,
            existing=tuple(
                (existing_file_record.path, existing_file_record.text)
                for existing_file_record in read_composition_response.target.files
            ),
            printed=render_composition_request.printed,
        )


class MapToRenderedTreeSpecWhenChecked(ts.Mapper, domain.RenderedTreeSpec):

    def __init__(self, read_composition_response: ports.ReadCompositionResponse) -> None:
        super().__init__(
            documents=tuple(
                (document_record.name, document_record.state.value, document_record.text)
                for document_record in read_composition_response.documents
            ),
            pieces=tuple((piece_record.path, piece_record.text) for piece_record in read_composition_response.pieces),
            target=read_composition_response.target.state.value,
            existing=tuple(
                (existing_file_record.path, existing_file_record.text)
                for existing_file_record in read_composition_response.target.files
            ),
            printed=(),
        )


class MapToWriteRenderingRequest(ts.Mapper, ports.WriteRenderingRequest):

    def __init__(self, render_composition_request: client.RenderCompositionRequest, rendered_tree: domain.RenderedTree) -> None:
        super().__init__(
            out_dir=render_composition_request.out_dir,
            files=tuple(
                ports.FileRecord(path=str(rendered_file.path()), text=str(rendered_file.content()))
                for rendered_file in rendered_tree.files()
            ),
        )


class MapToRenderCompositionResponseWhenWritten(ts.Mapper, client.RenderCompositionResponse):

    def __init__(self, write_rendering_response: ports.WriteRenderingResponse, rendered_tree: domain.RenderedTree) -> None:
        super().__init__(
            problems=tuple(
                f"{path} resolves outside the output directory, so nothing is written"
                for path in write_rendering_response.refused
            ),
            written=write_rendering_response.paths,
            kept=tuple(str(text) for text in rendered_tree.kept()),
            printed=tuple(
                client.PrintedFile(path=str(rendered_file.path()), text=str(rendered_file.content()))
                for rendered_file in rendered_tree.printed()
            ),
        )


class MapToRenderCompositionResponseWithProblems(ts.Mapper, client.RenderCompositionResponse):

    def __init__(self, rendered_tree: domain.RenderedTree) -> None:
        super().__init__(problems=tuple(str(text) for text in rendered_tree.problems()), written=(), kept=(), printed=())


class MapToReadCompositionRequestWhenChecked(ts.Mapper, ports.ReadCompositionRequest):

    def __init__(self, check_composition_request: client.CheckCompositionRequest) -> None:
        super().__init__(
            composition_dir=check_composition_request.composition_dir,
            out_dir=check_composition_request.tree_dir,
        )


class MapToCheckCompositionResponse(ts.Mapper, client.CheckCompositionResponse):

    def __init__(self, rendered_tree: domain.RenderedTree) -> None:
        super().__init__(
            problems=tuple(str(text) for text in rendered_tree.faults()),
            drifted=tuple(str(text) for text in rendered_tree.drift()),
            checked=len(rendered_tree.files()) + len(rendered_tree.kept()),
        )


class RenderingService(ts.ApplicationService):

    def __init__(self, composition_reader: ports.CompositionReader, rendering_writer: ports.RenderingWriter) -> None:
        self._composition_reader = composition_reader
        self._rendering_writer = rendering_writer

    def render_composition(
        self, render_composition_request: client.RenderCompositionRequest
    ) -> client.RenderCompositionResponse:
        read_composition_response = self._composition_reader.read_composition(
            MapToReadCompositionRequest(render_composition_request)
        )
        rendered_tree = domain.RenderedTree(MapToRenderedTreeSpec(read_composition_response, render_composition_request))
        match rendered_tree.health():
            case domain.Health.CLEAN:
                write_rendering_response = self._rendering_writer.write_rendering(
                    MapToWriteRenderingRequest(render_composition_request, rendered_tree)
                )
                return MapToRenderCompositionResponseWhenWritten(write_rendering_response, rendered_tree)
            case domain.Health.PROBLEMS:
                return MapToRenderCompositionResponseWithProblems(rendered_tree)
            case _ as never:
                typing.assert_never(never)

    def check_composition(self, check_composition_request: client.CheckCompositionRequest) -> client.CheckCompositionResponse:
        read_composition_response = self._composition_reader.read_composition(
            MapToReadCompositionRequestWhenChecked(check_composition_request)
        )
        rendered_tree = domain.RenderedTree(MapToRenderedTreeSpecWhenChecked(read_composition_response))
        return MapToCheckCompositionResponse(rendered_tree)
