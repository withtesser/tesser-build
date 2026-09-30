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
        assert completed.stderr == "missing argument <out-dir>\nusage: python -m srv.cli.render [--check] <composition-dir> <out-dir> [--print <rendered-path-or-pattern>]...\n"

    def test_a_printed_path_follows_the_list_with_its_header_and_the_file_as_written(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [
                sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "story-drafting"), str(tmp_path / "out"),
                "--print", "tests/test_reading_jtbds_by_jtbd_id.py", "--print", "tests/test_submitting_jtbds.py",
            ],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 0, completed.stderr
        listed, reading, submitting = completed.stdout.split("\n\n--- ")
        assert "tests/test_reading_jtbds_by_jtbd_id.py" in listed.splitlines()
        assert reading == "tests/test_reading_jtbds_by_jtbd_id.py\n" + (tmp_path / "out" / "tests" / "test_reading_jtbds_by_jtbd_id.py").read_text().removesuffix("\n")
        assert submitting == "tests/test_submitting_jtbds.py\n" + (tmp_path / "out" / "tests" / "test_submitting_jtbds.py").read_text()

    def test_a_printed_path_it_does_not_render_exits_one_and_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [
                sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "library"), str(tmp_path / "out"),
                "--print", "tests/test_nope.py",
            ],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert (completed.returncode, completed.stdout) == (1, "")
        assert completed.stderr == "render: --print names tests/test_nope.py, which the composition does not render\n"
        assert not (tmp_path / "out").exists()

    def test_a_root_test_skeleton_edited_by_its_author_is_kept_by_the_next_render(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        render = [sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "library"), str(tmp_path / "out")]
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        subprocess.run(render, capture_output=True, text=True, check=True, env=env)
        skeleton = tmp_path / "out" / "tests" / "test_reading_loans_by_loan_id.py"
        written = skeleton.read_text().replace("assert False, ", "assert True, ")
        skeleton.write_text(written)

        completed = subprocess.run(render, capture_output=True, text=True, check=False, env=env)

        assert completed.returncode == 0, completed.stderr
        assert "kept tests/test_reading_loans_by_loan_id.py" in completed.stdout.splitlines()
        assert skeleton.read_text() == written

    def test_a_tree_rendered_beside_its_own_specs_keeps_every_file_it_does_not_write(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        library = tmp_path / "library"
        (library / "specs").mkdir(parents=True)
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
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

    def test_an_unmarked_file_where_a_generated_one_goes_exits_one_and_writes_nothing(self, tmp_path: pathlib.Path) -> None:
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
            "render: the output directory already has loans/__init__.py, which is not marked generated, "
            "so the renderer will not replace it\n"
        )
        assert not (tmp_path / "library" / "app").exists()

    def test_rendering_again_overwrites_an_edited_generated_file_and_keeps_an_edited_agent_owned_one(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        library = tmp_path / "library"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        render = [sys.executable, "-m", "srv.cli.render", str(tree / "compositions" / "library"), str(library)]
        subprocess.run(render, capture_output=True, text=True, check=True, env=env)
        generated = library / "loans" / "client" / "client.py"
        owned = library / "loans" / "domain" / "loan.py"
        rendered = generated.read_text()
        generated.write_text(rendered + "\n")
        owned.write_text(owned.read_text() + "\n")

        completed = subprocess.run(render, capture_output=True, text=True, check=False, env=env)

        assert (completed.returncode, completed.stderr) == (0, "")
        assert generated.read_text() == rendered
        assert owned.read_text().endswith("\n\n")
        assert "kept loans/domain/loan.py" in completed.stdout.splitlines()

    def test_a_check_passes_on_a_fresh_render_and_fails_naming_each_generated_file_that_drifted(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        library = tmp_path / "library"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        composition = str(tree / "compositions" / "library")
        subprocess.run([sys.executable, "-m", "srv.cli.render", composition, str(library)], capture_output=True, check=True, env=env)
        check = [sys.executable, "-m", "srv.cli.render", "--check", composition, str(library)]

        fresh = subprocess.run(check, capture_output=True, text=True, check=False, env=env)
        (library / "loans" / "client" / "client.py").write_text(
            (library / "loans" / "client" / "client.py").read_text() + "\n"
        )
        (library / "loans" / "component" / "component.py").unlink()
        (library / "loans" / "client" / "__init__.py").write_text(
            (library / "loans" / "client" / "__init__.py").read_text().split("\n", 1)[1]
        )
        (library / "loans" / "domain" / "loan.py").write_text("the agent's own\n")
        drifted = subprocess.run(check, capture_output=True, text=True, check=False, env=env)

        assert fresh.returncode == 0, fresh.stderr
        assert fresh.stdout.startswith("check: ")
        assert (drifted.returncode, drifted.stdout) == (1, "")
        assert drifted.stderr.splitlines() == [
            "check: loans/client/__init__.py has lost its generated mark",
            "check: loans/client/client.py differs from what the composition renders",
            "check: loans/component/component.py is missing",
        ]

    def test_a_name_that_is_not_a_name_is_refused_before_anything_is_written(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        answered: dict[str, tuple[int, str, bool]] = {}
        for replaced, replacement in (
            ('context = "loans"', 'context = "../escape"'),
            ('context = "loans"', 'context = "app"'),
            ('name = "Loan"', 'name = "loan"'),
            ('[ports.NoticeSender]', '[ports."Notice/Sender"]'),
        ):
            composition = tmp_path / str(len(answered)) / "composition"
            composition.mkdir(parents=True)
            for name in ("language", "story", "infra", "composition", "implementations", "generator"):
                text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
                (composition / f"{name}.toml").write_text(text.replace(replaced, replacement) if name == "composition" else text)
            completed = subprocess.run(
                [sys.executable, "-m", "srv.cli.render", str(composition), str(tmp_path / str(len(answered)) / "out")],
                capture_output=True, text=True, check=False, env=env,
            )
            answered[replacement] = (completed.returncode, completed.stderr.strip(), (tmp_path / str(len(answered)) / "out").exists())

        assert answered == {
            'context = "../escape"': (1, "render: context names '../escape', which is not a snake_case name, like loan_id", False),
            'context = "app"': (1, "render: context names 'app', a name the rendered tree already uses for its own package", False),
            'name = "loan"': (1, "render: [aggregate] name names 'loan', which is not a PascalCase name, like LoanRepository", False),
            '[ports."Notice/Sender"]': (1, "render: [ports] names 'Notice/Sender', which is not a PascalCase name, like LoanRepository", False),
        }
