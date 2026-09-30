from __future__ import annotations

import pathlib

import rendering.adapters.repositories as repositories
import rendering.application.ports as ports


class TestFilesystemCompositionReader:

    def test_each_document_is_read_or_named_missing_and_each_piece_is_read_by_its_path(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "composition").mkdir()
        (tmp_path / "composition" / "language.toml").write_text('context = "lending"\n')
        (tmp_path / "pieces" / "{{context}}").mkdir(parents=True)
        (tmp_path / "pieces" / "{{context}}" / "note.txt.tmpl").write_text("{{context}}\n")

        read_composition_response = repositories.FilesystemCompositionReader(str(tmp_path / "pieces")).read_composition(
            ports.ReadCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"))
        )

        assert [(document.name, document.state, document.text) for document in read_composition_response.documents] == [
            ("language", ports.DocumentState.READ, 'context = "lending"\n'),
            ("story", ports.DocumentState.MISSING, ""),
            ("composition", ports.DocumentState.MISSING, ""),
            ("implementations", ports.DocumentState.MISSING, ""),
            ("generator", ports.DocumentState.MISSING, ""),
        ]
        assert [(piece.path, piece.text) for piece in read_composition_response.pieces] == [
            ("{{context}}/note.txt.tmpl", "{{context}}\n")
        ]
        assert read_composition_response.target.state == ports.TargetState.ABSENT

    def test_an_existing_output_directory_is_read_file_by_file(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "out" / "lending").mkdir(parents=True)
        (tmp_path / "out" / "lending" / "loan.py").write_text("class Loan:\n")

        read_composition_response = repositories.FilesystemCompositionReader(str(tmp_path / "pieces")).read_composition(
            ports.ReadCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"))
        )

        assert read_composition_response.target.state == ports.TargetState.OCCUPIED
        assert [(found.path, found.text) for found in read_composition_response.target.files] == [
            ("lending/loan.py", "class Loan:\n")
        ]

    def test_an_output_path_that_is_a_file_is_named_so(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "out").write_text("")

        read_composition_response = repositories.FilesystemCompositionReader(str(tmp_path / "pieces")).read_composition(
            ports.ReadCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"))
        )

        assert read_composition_response.target.state == ports.TargetState.NOT_DIRECTORY

    def test_a_composition_in_the_output_directorys_repo_is_named_from_the_repo_root(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "repo" / ".git").mkdir(parents=True)
        (tmp_path / "repo" / "generator" / "compositions" / "lending").mkdir(parents=True)

        read_composition_response = repositories.FilesystemCompositionReader(str(tmp_path / "pieces")).read_composition(
            ports.ReadCompositionRequest(
                composition_dir=str(tmp_path / "repo" / "generator" / "compositions" / "lending"),
                out_dir=str(tmp_path / "repo" / "lending"),
            )
        )

        assert read_composition_response.composition == "generator/compositions/lending"

    def test_a_composition_outside_the_output_directorys_repo_is_named_by_its_absolute_path(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "repo" / ".git").mkdir(parents=True)
        (tmp_path / "compositions" / "lending").mkdir(parents=True)

        read_composition_response = repositories.FilesystemCompositionReader(str(tmp_path / "pieces")).read_composition(
            ports.ReadCompositionRequest(composition_dir=str(tmp_path / "compositions" / "lending"), out_dir=str(tmp_path / "repo" / "lending"))
        )

        assert read_composition_response.composition == (tmp_path / "compositions" / "lending").resolve().as_posix()
