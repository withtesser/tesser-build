from __future__ import annotations

import os
import pathlib
import subprocess
import sys


class TestGeneratingTrees:

    def test_every_committed_spec_generates_every_template_and_exits_zero(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[1]
        template_count = len(list((tree / "templates").rglob("*.tmpl")))

        answered = {
            spec.stem: subprocess.run(
                [sys.executable, "-m", "srv.cli.generate", str(spec), str(tmp_path / spec.stem)],
                cwd=tree,
                env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tree), str(tree.parent / "tesser-py")])},
                capture_output=True,
                text=True,
            )
            for spec in sorted((tree / "specs").glob("*.toml"))
        }

        assert answered
        assert {name: (result.returncode, result.stderr) for name, result in answered.items()} == {
            name: (0, "") for name in answered
        }
        assert {name: len(result.stdout.splitlines()) for name, result in answered.items()} == {
            name: template_count for name in answered
        }
        assert {
            name: sorted(path.relative_to(tmp_path / name).as_posix() for path in (tmp_path / name).rglob("*") if path.is_file())
            for name in answered
        } == {name: sorted(result.stdout.splitlines()) for name, result in answered.items()}
