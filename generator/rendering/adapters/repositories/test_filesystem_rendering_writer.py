from __future__ import annotations

import pathlib

import rendering.adapters.repositories as repositories
import rendering.application.ports as ports


class TestFilesystemRenderingWriter:

    def test_every_file_is_written_under_the_output_directory_at_its_path(self, tmp_path: pathlib.Path) -> None:
        write_rendering_response = repositories.FilesystemRenderingWriter().write_rendering(
            ports.WriteRenderingRequest(
                out_dir=str(tmp_path / "out"),
                files=(
                    ports.FileRecord(path=".tesser-root", text="app\n"),
                    ports.FileRecord(path="lending/domain/loan.py", text="class Loan:\n"),
                ),
            )
        )

        assert (tmp_path / "out" / ".tesser-root").read_text() == "app\n"
        assert (tmp_path / "out" / "lending" / "domain" / "loan.py").read_text() == "class Loan:\n"
        assert write_rendering_response.paths == (".tesser-root", "lending/domain/loan.py")
        assert write_rendering_response.refused == ()

    def test_a_path_that_resolves_outside_the_output_directory_is_refused_and_nothing_is_written(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / "out").mkdir()
        (tmp_path / "elsewhere").mkdir()
        (tmp_path / "out" / "linked").symlink_to(tmp_path / "elsewhere")

        write_rendering_response = repositories.FilesystemRenderingWriter().write_rendering(
            ports.WriteRenderingRequest(
                out_dir=str(tmp_path / "out"),
                files=(
                    ports.FileRecord(path="lending/loan.py", text="class Loan:\n"),
                    ports.FileRecord(path="../escape.py", text="x\n"),
                    ports.FileRecord(path="linked/escape.py", text="x\n"),
                ),
            )
        )

        assert write_rendering_response.refused == ("../escape.py", "linked/escape.py")
        assert write_rendering_response.paths == ()
        assert not (tmp_path / "out" / "lending").exists()
        assert not (tmp_path / "escape.py").exists()
        assert not (tmp_path / "elsewhere" / "escape.py").exists()
