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
            [sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "story-drafting")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 2
        assert completed.stderr == "missing argument <out-dir>\nusage: python -m srv.cli.render <composition-dir> <out-dir>\n"
