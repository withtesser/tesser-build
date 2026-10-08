from __future__ import annotations

import tesser.testing as ts

import rendering.application as application
import rendering.application.ports as ports
import rendering.client as client


@ts.fake
class FakeCompositionReader(ports.CompositionReader):

    def __init__(self, documents: tuple[ports.DocumentRecord, ...], pieces: tuple[ports.PieceRecord, ...]) -> None:
        self._documents = documents
        self._pieces = pieces
        self.asked: list[ports.ReadCompositionRequest] = []

    def read_composition(self, read_composition_request: ports.ReadCompositionRequest) -> ports.ReadCompositionResponse:
        self.asked.append(read_composition_request)
        return ports.ReadCompositionResponse(
            documents=self._documents,
            pieces=self._pieces,
            target=ports.TargetRecord(state=ports.TargetState.ABSENT, files=()),
            composition="compositions/lending",
        )


@ts.fake
class FakeRenderingWriter(ports.RenderingWriter):

    def __init__(self) -> None:
        self.written: list[ports.WriteRenderingRequest] = []

    def write_rendering(self, write_rendering_request: ports.WriteRenderingRequest) -> ports.WriteRenderingResponse:
        self.written.append(write_rendering_request)
        return ports.WriteRenderingResponse(
            paths=tuple(file_record.path for file_record in write_rendering_request.files),
            removed=write_rendering_request.removed, refused=(),
        )


class TestRenderingService:

    def test_a_composition_whose_documents_are_missing_answers_its_problems_and_writes_nothing(self) -> None:
        fake_rendering_writer = FakeRenderingWriter()
        rendering_service = application.RenderingService(
            FakeCompositionReader(
                documents=tuple(
                    ports.DocumentRecord(name=name, state=ports.DocumentState.MISSING, text="")
                    for name in ("language", "story", "infra", "composition", "implementations", "generator")
                ),
                pieces=(),
            ),
            fake_rendering_writer,
        )

        render_composition_response = rendering_service.render_composition(
            client.RenderCompositionRequest(composition_dir="/compositions/lending", out_dir="/out", printed=())
        )

        assert render_composition_response.problems == (
            "the composition's language.toml is missing",
            "the composition's story.toml is missing",
            "the composition's infra.toml is missing, and it says what the app runs on and what an operator must provide",
            "the composition's composition.toml is missing",
            "the composition's implementations.toml is missing",
            "the composition's generator.toml is missing",
        )
        assert fake_rendering_writer.written == []

    def test_the_request_names_the_composition_and_the_output_it_reads(self) -> None:
        fake_composition_reader = FakeCompositionReader(documents=(), pieces=())

        application.RenderingService(fake_composition_reader, FakeRenderingWriter()).render_composition(
            client.RenderCompositionRequest(composition_dir="/compositions/lending", out_dir="/out", printed=())
        )

        assert [
            (read_composition_request.composition_dir, read_composition_request.out_dir)
            for read_composition_request in fake_composition_reader.asked
        ] == [("/compositions/lending", "/out")]

    def test_a_check_reads_the_tree_it_names_and_answers_the_problems_it_meets(self) -> None:
        fake_composition_reader = FakeCompositionReader(documents=(), pieces=())

        check_composition_response = application.RenderingService(fake_composition_reader, FakeRenderingWriter()).check_composition(
            client.CheckCompositionRequest(composition_dir="/compositions/lending", tree_dir="/tree")
        )

        assert [(asked.composition_dir, asked.out_dir) for asked in fake_composition_reader.asked] == [
            ("/compositions/lending", "/tree")
        ]
        assert check_composition_response.problems[0] == "the composition has no language.toml"
        assert check_composition_response.drifted == ()
