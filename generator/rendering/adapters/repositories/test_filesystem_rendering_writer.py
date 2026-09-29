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
