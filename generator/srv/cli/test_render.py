from __future__ import annotations

import os
import pathlib
import subprocess
import sys


class TestRenderHost:

    def test_every_composition_renders_and_exits_zero_listing_what_it_wrote(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        compositions = sorted(path for path in (tree / "compositions").iterdir() if path.is_dir())

        answered = {
            composition.name: subprocess.run(
                [sys.executable, "-m", "srv.cli.render", str(composition), str(tmp_path / composition.name)],
                capture_output=True, text=True, check=False,
                env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
            )
            for composition in compositions
        }

        assert compositions
        assert {name: (completed.returncode, completed.stderr) for name, completed in answered.items()} == {
            name: (0, "") for name in answered
        }
        assert all(".tesser-root" in completed.stdout.splitlines() for completed in answered.values())

    def test_a_missing_output_directory_argument_exits_two_with_the_usage(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "library")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 2
        assert completed.stderr == "missing argument <out-dir>\nusage: python -m srv.cli.render <composition-dir> <out-dir>\n"

    def test_a_tree_rendered_beside_its_own_specs_keeps_every_file_it_does_not_write(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        library = tmp_path / "library"
        (library / "specs").mkdir(parents=True)
        for name in ("language", "story", "composition", "implementations", "generator"):
            (library / "specs" / f"{name}.toml").write_text((tree / "compositions" / "library" / f"{name}.toml").read_text())
        (library / "README.md").write_text("# library\n")

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.render", str(library / "specs"), str(library)],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )
        again = subprocess.run(
            [sys.executable, "-m", "srv.cli.render", str(library / "specs"), str(library)],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert (completed.returncode, completed.stderr) == (0, "")
        assert "loans/adapters/handlers/http.py" in completed.stdout.splitlines()
        assert (library / "loans" / "adapters" / "handlers" / "http.py").is_file()
        assert (library / "README.md").read_text() == "# library\n"
        assert (again.returncode, again.stdout) == (0, completed.stdout)

    def test_a_file_it_would_write_differently_exits_one_and_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "library" / "loans").mkdir(parents=True)
        (tmp_path / "library" / "loans" / "__init__.py").write_text("hand written\n")

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "library"), str(tmp_path / "library")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert (completed.returncode, completed.stdout) == (1, "")
        assert completed.stderr == (
            "render: the output directory already has loans/__init__.py, which the renderer would write differently\n"
        )
        assert not (tmp_path / "library" / "app").exists()
