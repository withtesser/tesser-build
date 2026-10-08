from __future__ import annotations

import ast
import os
import pathlib
import subprocess
import sys

import rendering.client as client
import rendering.component as component


class TestRenderingCompositions:

    def test_two_client_operations_reusing_one_repository_operation_render_one_mapper_each(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}/title\"\nthen = \"I get back 200 with its title\"\nroute = \"GET /loans/{loan_id}/title\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.get_title]\nrequest = [\"loan_id\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/application"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        service = (tmp_path / "out" / "loans" / "application" / "loan_service.py").read_text()
        assert "class MapToLoadLoanRequest(" in service
        assert "class MapToLoadLoanRequestForGetTitle(" in service

    def test_a_load_keeps_what_the_steps_before_it_hold(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I PUT a title as JSON to /loans/{loan_id}\"\nthen = \"I get back 200 with its title\"\nroute = \"PUT /loans/{loan_id}\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.retitle_loan]\nrequest = [\"loan_id\", \"title\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\", \"repository.save_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/application", "srv/http/test_main.py", "-k", "not discovers"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        service = (tmp_path / "out" / "loans" / "application" / "loan_service.py").read_text()
        assert "title=retitle_loan_request.title," in service

    def test_a_port_annotation_types_its_own_operation_only(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [(
                'operations.send_notice = { request = ["borrower", "title"], response = [] }',
                'operations.send_notice = { request = ["borrower", "title"], response = ["copies: int"] }\n'
                'operations.recall_notice = { request = ["copies: str"], response = [] }',
            )],
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        port = ast.parse((tmp_path / "out" / "loans" / "application" / "ports" / "notice_sender.py").read_text())
        annotations = {
            (node.name, arg.arg): ast.unparse(arg.annotation)
            for node in port.body
            if isinstance(node, ast.ClassDef)
            for method in node.body
            if isinstance(method, ast.FunctionDef) and method.name == "__init__"
            for arg in method.args.args
            if arg.annotation is not None
        }
        assert (annotations[("SendNoticeResponse", "copies")], annotations[("RecallNoticeRequest", "copies")]) == ("int", "str")

    def test_calls_on_names_only_outcomes_of_the_command(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ("[aggregate.reads]", "[aggregate.commands.renew_loan]\ntakes = { title = \"str\" }\noutcomes = [\"renewed\", \"refused\"]\n\n[aggregate.reads]"),
                ('builds = "Loan"\ncalls = "save_loan"', 'builds = "Loan"\ncommands = ["renew_loan"]\ncalls_on = ["renewd"]\ncalls = "save_loan"'),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "actions.loan.operations.record_loan calls_on names 'renewd', which is not an outcome of renew_loan",
        )

    def test_an_int_field_crosses_every_layer_as_an_int(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ('[aggregate.spec]\nloan_id = "str"', '[aggregate.spec]\ncopies = "int"\nloan_id = "str"'),
                ('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\ncopies = "int"\nloan_id = "str"'),
                ('request = ["borrower", "title"]\nresponse = ["loan_id"]', 'request = ["borrower", "title", "copies"]\nresponse = ["loan_id"]'),
                ('response = ["loan_id", "borrower", "title"]', 'response = ["loan_id", "borrower", "title", "copies"]'),
                ('[orchestrator.operations.arrange_loan]\nrequest = ["loan_id", "borrower", "title"]', '[orchestrator.operations.arrange_loan]\nrequest = ["loan_id", "borrower", "title", "copies"]'),
                ('[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title"]', '[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title", "copies"]'),
            ],
            "story.toml": [
                ('given = "a borrower and a title"', 'given = "a borrower, a title, and copies"'),
                ('then = "I get back 200 with its borrower and title"', 'then = "I get back 200 with its borrower, title, and copies"'),
            ],
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/domain", "loans/application"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert "str(loan.copies)" not in (tmp_path / "out" / "loans" / "application" / "loan_service.py").read_text()

    def test_a_snapshot_is_never_asked_to_refuse_a_message_it_should_read(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ('[aggregate.spec]\nloan_id = "str"', '[aggregate.spec]\ncopies = "int"\nloan_id = "str"'),
                ('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\ncopies = "int"\nloan_id = "str"'),
                ('request = ["borrower", "title"]\nresponse = ["loan_id"]', 'request = ["borrower", "title", "copies"]\nresponse = ["loan_id"]'),
                ('[orchestrator.operations.arrange_loan]\nrequest = ["loan_id", "borrower", "title"]', '[orchestrator.operations.arrange_loan]\nrequest = ["copies", "loan_id", "borrower", "title"]'),
                ('calls = "send_notice"\nrequest = ["loan_id", "borrower", "title"]\nresponse = ["loan_id"]', 'calls = "send_notice"\nrequest = ["loan_id", "borrower", "title"]\nresponse = []'),
                ('[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title"]', '[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title", "copies"]'),
            ],
            "story.toml": [
                ('given = "a borrower and a title"', 'given = "a borrower, a title, and copies"'),
                ('then = "I get back 200 with its borrower and title"', 'then = "I get back 200 with its borrower, title, and copies"'),
            ],
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/application/relays"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout

    def test_several_operations_on_one_class_of_actions_render_one_fake_per_application_client(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ('steps = ["actions.notice.send_notice", "actions.loan.record_loan", "signal.await_return_book"]', 'steps = ["actions.notice.send_notice", "actions.loan.record_loan", "actions.loan.note_loan", "signal.await_return_book"]'),
                ("[ports.NoticeSender]", "[actions.loan.operations.note_loan]\nbuilds = \"Loan\"\ncalls = \"save_loan\"\nrequest = [\"loan_id\", \"borrower\", \"title\"]\nresponse = [\"loan_id\"]\n\n[ports.NoticeSender]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/application"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        defined = {
            path.relative_to(tmp_path / "out").as_posix(): [node.name for node in ast.parse(path.read_text()).body if isinstance(node, ast.ClassDef)]
            for path in (tmp_path / "out" / "loans" / "adapters").rglob("test_*.py")
        }
        assert {path: names for path, names in defined.items() if len(names) != len(set(names))} == {}

    def test_an_action_the_orchestrator_never_runs_is_a_problem_not_a_crash(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ("[ports.NoticeSender]", "[actions.loan.operations.note_loan]\nbuilds = \"Loan\"\ncalls = \"save_loan\"\nrequest = [\"loan_id\", \"borrower\", \"title\"]\nresponse = [\"loan_id\"]\n\n[ports.NoticeSender]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "actions.loan.operations.note_loan is never run by the orchestrator, so nothing reaches it",
        )

    def test_two_ports_implemented_by_one_class_render_one_path_twice_and_are_refused(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [("[ports.LoanRepository]", "[ports.ReminderSender]\noperations.send_reminder = { request = [\"borrower\"], response = [] }\n\n[ports.LoanRepository]")],
            "implementations.toml": [
                ("[implementations.LoanRepository.memory]", "[implementations.ReminderSender.printed]\nclass = \"PrintedNoticeSender\"\nbody = \"agent\"\n\n[implementations.LoanRepository.memory]"),
                ('NoticeSender = "printed", ', 'NoticeSender = "printed", ReminderSender = "printed", '),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert "two pieces render loans/adapters/gateways/printed_notice_sender.py, and a render writes each path once" in (
            render_composition_response.problems
        )
        assert not (tmp_path / "out").exists()

    def test_every_environment_names_an_implementation_for_every_port(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[environments.gate]",
                "[environments.local]\nimplementations = { LoanRepository = \"memory\", LoanIdentityRepository = \"uuid\" }\n"
                "engine = \"restate\"\nhosts = [\"http\"]\n\n[environments.gate]",
            )],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "environment local names no implementation for NoticeSender",
        )

    def test_a_route_no_client_operation_serves_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I DELETE /loans/{loan_id}\"\nthen = \"I get back 204\"\nroute = \"DELETE /loans/{loan_id}\"\nstatus = 204\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("s-1-c-1 has a route, and no client operation serves it",)

    def test_a_client_operation_serving_two_routed_stories_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [('serves = ["s-1", "s-1-a-1"]', 'serves = ["s-1", "s-1-a-1", "s-1-b-1"]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "client operation lend_book serves 2 level-2 stories with a route; it serves exactly one, whose route it is",
        )

    def test_a_route_its_own_story_does_not_state_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('route = "POST /loans"', 'route = "PUT /loans"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "s-1-a-1 is PUT /loans answering 201, and its own when and then do not say so "
            "(when: 'I POST them as JSON to /loans'; then: 'I get back 201 with its loan_id')",
        )

    def test_a_story_states_its_route_and_status_with_punctuation_around_them(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [
                ('when = "I POST them as JSON to /loans"', 'when = "I POST them as JSON (to /loans)."'),
                ('then = "I get back 201 with its loan_id"', 'then = "I get back 201, with its loan_id."'),
                ('when = "I GET /loans/{loan_id}"', 'when = "I GET /loans/{loan_id}, by its loan_id."'),
                ('then = "I get back 200 with its borrower and title"', 'then = "I get back (200) with its borrower and title."'),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()

    def test_a_path_the_story_states_only_inside_a_longer_path_is_not_stated(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('when = "I POST them as JSON to /loans"', 'when = "I POST them as JSON to /loans/new."')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "s-1-a-1 is POST /loans answering 201, and its own when and then do not say so "
            "(when: 'I POST them as JSON to /loans/new.'; then: 'I get back 201 with its loan_id')",
        )

    def test_a_class_of_actions_named_for_its_port_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ("[actions.story]", "[actions.drafter]"),
                ("[actions.story.operations.draft_stories]", "[actions.drafter.operations.draft_stories]"),
                ('"actions.story.draft_stories"', '"actions.drafter.draft_stories"'),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "story-drafting" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "[actions.drafter] is named for 'Drafter', which is neither a term nor a code name in language.toml; a class of "
            "actions is named for the domain term it acts on (a term's name or its short form), never for its port (StoryDrafter)",
        )

    def test_a_class_of_actions_is_named_for_a_term_or_its_short_form_with_no_code_names(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "composition").mkdir()
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "story-drafting" / f"{name}.toml").read_text()
            if name == "language":
                assert "code_names" not in text
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert "class StoryActions" in (tmp_path / "out" / "drafting" / "application" / "story_actions.py").read_text()
        assert "class JtbdActions" in (tmp_path / "out" / "drafting" / "application" / "jtbd_actions.py").read_text()

    def test_a_class_of_actions_named_for_the_term_it_acts_on_renders(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "story-drafting"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert (tmp_path / "out" / "drafting" / "application" / "story_actions.py").is_file()

    def test_a_composition_without_infra_toml_is_a_problem_saying_what_it_holds(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "composition").mkdir()
        for name in ("language", "story", "composition", "implementations", "generator"):
            (tmp_path / "composition" / f"{name}.toml").write_text((tree / "compositions" / "library" / f"{name}.toml").read_text())
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "the composition's infra.toml is missing, and it says what the app runs on and what an operator must provide",
        )
        assert not (tmp_path / "out").exists()

    def test_an_implementations_toml_still_carrying_engine_hosts_variables_or_app_is_a_problem_saying_they_moved(
        self, tmp_path: pathlib.Path,
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[implementations.NoticeSender.printed]",
                'app = "library"\n\n[implementations.NoticeSender.printed]',
            ), (
                "[environments.gate]",
                '[engine.restate]\nengine_url_variable = "RESTATE_URL"\n\n[hosts.http]\n'
                'listen_port_variable = "LIBRARY_PORT"\n\n[variables]\nLIBRARY_PORT = "the port"\n\n[environments.gate]',
            )],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "implementations.toml declares app, which moved to infra.toml: implementations.toml holds only "
            "[implementations] and [environments]",
            "implementations.toml declares [engine], which moved to infra.toml: implementations.toml holds only "
            "[implementations] and [environments]",
            "implementations.toml declares [hosts], which moved to infra.toml: implementations.toml holds only "
            "[implementations] and [environments]",
            "implementations.toml declares [variables], which moved to infra.toml: implementations.toml holds only "
            "[implementations] and [environments]",
        )

    def test_a_store_implemented_by_a_storage_infra_toml_does_not_declare_is_a_problem_naming_both(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"infra.toml": [("[storage.memory]", "[storage.sqlite]\nlocation_variable = \"LOAN_DB_PATH\"")]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "LoanRepository is a store implemented by memory, a storage infra.toml does not declare: "
            "declare [storage.memory] in infra.toml, or implement LoanRepository by a declared storage",
        )

    def test_a_storage_other_than_memory_without_a_location_variable_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"infra.toml": [("[storage.memory]", "[storage.memory]\n\n[storage.sqlite]")]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "[storage.sqlite] names no location_variable: every storage but memory says which variable locates it",
        )

    def test_an_engine_admin_variable_is_a_problem_because_the_tests_take_the_admin_url_as_a_fixture(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"infra.toml": [('engine_url_variable = "RESTATE_URL"\n', 'engine_url_variable = "RESTATE_URL"\nadmin_variable = "RESTATE_ADMIN"\n')]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "[engine.restate] names admin_variable, which nothing reads: the tests take the engine's admin URL and callback "
            "host from the root conftest's fixtures, so infra.toml names no variable for them",
        )

    def test_a_declared_storage_no_port_uses_renders(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"infra.toml": [("[storage.memory]", "[storage.memory]\n\n[storage.sqlite]\nlocation_variable = \"LOAN_DB_PATH\"")]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert "LOAN_DB_PATH" not in (tmp_path / "out" / "app" / "app.py").read_text()

    def test_an_agent_owned_store_renders_a_working_store_stub_the_component_wires_and_keeps_it_on_a_second_render(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[implementations.LoanRepository.memory]\nbody = \"supported\"",
                "[implementations.LoanRepository.file]\nclass = \"FileLoanStore\"\nbody = \"agent\"",
            ), ('LoanRepository = "memory"', 'LoanRepository = "file"')],
            "infra.toml": [("[storage.memory]", "[storage.file]\nlocation_variable = \"LOAN_FILE\"")],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(render_composition_request)
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/adapters/repositories", "loans/component"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "loans"], cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        store_path = tmp_path / "out" / "loans" / "adapters" / "repositories" / "file_loan_store.py"
        edited = store_path.read_text().replace(
            "    def __init__(self, location: str) -> None:\n", "    def __init__(self, location: str) -> None:\n        self._location = location\n"
        )
        store_path.write_text(edited)
        second_response = rendering.client.render_composition(render_composition_request)
        check_composition_response = rendering.client.check_composition(
            client.CheckCompositionRequest(composition_dir=str(tmp_path / "composition"), tree_dir=str(tmp_path / "out")),
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        assert store_path.read_text().startswith("# pragma: tesser-agent-owned; rendered as a stub for you to write, and a render keeps each definition written here by hand\n")
        assert "class FileLoanStore(ts.Repository):" in store_path.read_text()
        assert "async def transaction(self)" in store_path.read_text()
        assert (tmp_path / "out" / "loans" / "adapters" / "repositories" / "test_file_loan_store.py").read_text().startswith(
            "# pragma: tesser-agent-owned;")
        assert not (tmp_path / "out" / "loans" / "adapters" / "repositories" / "memory_loan_repository.py").exists()
        assert "repositories.FileLoanStore(location=config.file_location)" in (tmp_path / "out" / "loans" / "component" / "component.py").read_text()
        assert store_path.read_text() == edited
        assert "loans/adapters/repositories/file_loan_store.py" in second_response.kept
        assert check_composition_response.problems == ()
        assert check_composition_response.drifted == ()

    def test_a_store_on_a_located_storage_is_built_with_the_location_its_variable_names(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[implementations.LoanRepository.memory]\nbody = \"supported\"",
                "[implementations.LoanRepository.sqlite]\nclass = \"SqliteLoanStore\"\nbody = \"agent\"",
            ), ('LoanRepository = "memory"', 'LoanRepository = "sqlite"')],
            "infra.toml": [("[storage.memory]", "[storage.sqlite]\nlocation_variable = \"LOAN_DB_PATH\"")],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/adapters/repositories", "loans/component", "app"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "loans", "app"], cwd=tmp_path / "out", capture_output=True, text=True,
            check=False, env=env,
        )
        store = (tmp_path / "out" / "loans" / "adapters" / "repositories" / "sqlite_loan_store.py").read_text()

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        assert "    def __init__(self, location: str) -> None:\n" in store
        assert "repositories.SqliteLoanStore(location=str(tmp_path / " in (
            tmp_path / "out" / "loans" / "adapters" / "repositories" / "test_sqlite_loan_store.py").read_text()
        assert "repositories.SqliteLoanStore(location=config.sqlite_location)" in (
            tmp_path / "out" / "loans" / "component" / "component.py").read_text()
        assert 'self._environ.get("LOAN_DB_PATH")' in (tmp_path / "out" / "app" / "app.py").read_text()
        assert '"LOAN_DB_PATH": str(locations / "sqlite_location"),' in (tmp_path / "out" / "conftest.py").read_text()

    def test_each_routed_story_renders_a_root_test_that_calls_its_route_and_asserts_its_status(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "story-drafting"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert sorted(path for path in render_composition_response.written if path.startswith("tests/")) == [
            "tests/__init__.py", "tests/test_reading_jtbds_by_jtbd_id.py", "tests/test_submitting_jtbds.py",
        ]
        reading = (tmp_path / "out" / "tests" / "test_reading_jtbds_by_jtbd_id.py").read_text()
        assert reading.startswith("# pragma: tesser-agent-owned;")
        assert "    def test_s_2_a_1(self, host: str) -> None:\n" in reading
        assert "tesser.testing" not in reading
        assert "served" not in reading
        assert '        jtbd_id: str = "jtbd-1"\n' in reading
        assert reading.index('jtbd_id: str = "jtbd-1"') < reading.index('f"{host}/jtbds/{jtbd_id}", data=None,')
        assert "reached_by" not in reading
        assert "time.sleep" not in reading
        assert "assert False" not in reading
        assert reading.rstrip().endswith(
            "assert status == 200, 's-2-a-1: given I have created a job to be done with POST /jtbds, and its stories have been drafted; "
            "then I get back 200 with status \"awaiting_story_acceptance\" and a stories list holding at least one story, "
            "each with a given, a when, and a then, and in state \"drafted\"' + f\" (answered {answered_body!r})\""
        )
        ast.parse(reading)

    def test_a_tree_with_root_tests_renders_a_root_conftest_whose_host_fixture_answers_pytest_s_host_option(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        )
        hosted = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "--host", "http://127.0.0.1:9"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        conftest = (tmp_path / "out" / "conftest.py").read_text()

        assert render_composition_response.problems == ()
        assert not (tmp_path / "out" / "tests" / "conftest.py").exists()
        assert conftest.startswith("# pragma: tesser-generated;")
        assert '    parser.addoption("--host", help="the base URL of a host already served; without it the run serves its own")\n' in conftest
        assert "def host(request: pytest.FixtureRequest) -> typing.Iterator[str]:\n" in conftest
        assert '"RESTATE_URL": f"http://{host_engine.get_container_host_ip()}:{host_engine.get_exposed_port(8080)}",' in conftest
        assert '"LIBRARY_PORT": str(port),' in conftest
        assert 'f"http://host.docker.internal:{port}/restate",' in conftest
        for fixture in ("engine_url", "engine_admin_url", "engine_callback_host", "free_port"):
            assert f"\ndef {fixture}(" in conftest
        assert (tmp_path / "out" / "tests" / "__init__.py").read_text().startswith("# pragma: tesser-generated;")
        assert "Connection refused" in hosted.stdout
        assert "could not register" not in hosted.stdout

    def test_a_route_with_no_path_value_binds_nothing_and_asserts_its_status_with_its_story(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        )
        submitting = (tmp_path / "out" / "tests" / "test_submitting_loans.py").read_text()

        assert (
            "    def test_s_1_a_1(self, host: str) -> None:\n        request = urllib_request.Request(\n"
        ) in submitting
        assert (
            "        assert status == 201, 's-1-a-1: given a borrower and a title; then I get back 201 with its loan_id' "
            "+ f\" (answered {answered_body!r})\"\n"
        ) in submitting
        assert "assert False" not in submitting
        ast.parse(submitting)

    def test_an_edited_root_test_skeleton_is_kept_on_render_again(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        rendering.client.render_composition(render_composition_request)
        reading = tmp_path / "out" / "tests" / "test_reading_loans_by_loan_id.py"
        reading.write_text(reading.read_text().replace('loan_id: str = "loan-1"', 'loan_id: str = "loan-2"'))
        edited = reading.read_text()

        render_composition_response = rendering.client.render_composition(render_composition_request)

        assert render_composition_response.problems == ()
        assert reading.read_text() == edited
        assert "tests/test_reading_loans_by_loan_id.py" in render_composition_response.kept

    def test_a_refusal_the_domain_raises_answers_422_with_its_message(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "library-direct"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        loan = tmp_path / "out" / "loans" / "domain" / "loan.py"
        loan.write_text(loan.read_text().replace("import tesser.domain as ts\n", "import tesser.domain as ts\nimport tesser.errors as errors\n").replace(
            "        self._borrower = spec.borrower\n",
            "        if not spec.borrower.strip():\n            raise errors.invalid(\"blank_borrower\", \"a loan needs a borrower\")\n"
            "        self._borrower = spec.borrower\n",
        ))
        (tmp_path / "out" / "tests" / "test_refusing.py").write_text(
            "import json\nimport urllib.error as urllib_error\nimport urllib.request as urllib_request\n\n\n"
            "class TestRefusing:\n\n    def test_a_blank_borrower_is_refused(self, host: str) -> None:\n"
            "        request = urllib_request.Request(f\"{host}/loans\", data=b'{\"borrower\": \" \", \"title\": \"Beloved\"}', "
            "headers={\"Content-Type\": \"application/json\"}, method=\"POST\")\n"
            "        try:\n            urllib_request.urlopen(request, timeout=30)\n            status, body = 201, b\"\"\n"
            "        except urllib_error.HTTPError as error:\n            status, body = error.code, error.read()\n"
            "        assert (status, json.loads(body)) == (422, {\"detail\": \"a loan needs a borrower\"})\n"
        )

        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_refusing.py", "loans/adapters/handlers", "loans/client"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout

    def test_a_store_the_composition_no_longer_renders_is_removed_when_it_renders_again(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text((tree / "compositions" / "library-direct" / f"{name}.toml").read_text())
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(
            composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=(),
        )
        rendering.client.render_composition(render_composition_request)
        for name, old, new in (
            ("implementations", "[implementations.LoanRepository.memory]\nbody = \"supported\"",
             "[implementations.LoanRepository.sqlite]\nclass = \"SqliteLoanStore\"\nbody = \"agent\""),
            ("implementations", 'LoanRepository = "memory"', 'LoanRepository = "sqlite"'),
            ("infra", "[storage.memory]", "[storage.sqlite]\nlocation_variable = \"LIBRARY_DB_PATH\""),
        ):
            text = (tmp_path / "composition" / f"{name}.toml").read_text()
            assert old in text
            (tmp_path / "composition" / f"{name}.toml").write_text(text.replace(old, new, 1))

        render_composition_response = rendering.client.render_composition(render_composition_request)
        check_composition_response = rendering.client.check_composition(
            client.CheckCompositionRequest(composition_dir=str(tmp_path / "composition"), tree_dir=str(tmp_path / "out")),
        )

        assert render_composition_response.problems == ()
        assert render_composition_response.removed == (
            "loans/adapters/repositories/memory_loan_repository.py", "loans/adapters/repositories/test_memory_loan_repository.py",
        )
        assert not (tmp_path / "out" / "loans" / "adapters" / "repositories" / "memory_loan_repository.py").exists()
        assert (tmp_path / "out" / "loans" / "adapters" / "repositories" / "sqlite_loan_store.py").is_file()
        assert check_composition_response.drifted == ()

    def test_a_root_test_whose_route_the_composition_no_longer_serves_is_removed_with_what_its_author_wrote(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text((tree / "compositions" / "library-direct" / f"{name}.toml").read_text())
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(
            composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=(),
        )
        rendering.client.render_composition(render_composition_request)
        reading = tmp_path / "out" / "tests" / "test_reading_loans_by_loan_id.py"
        reading.write_text(reading.read_text().replace('loan_id: str = "loan-1"', 'loan_id: str = "loan-2"'))
        story = (tmp_path / "composition" / "story.toml").read_text()
        (tmp_path / "composition" / "story.toml").write_text(story.split('[[jtbds.stories.jtbds]]\nid = "j-1-b"', 1)[0])
        composition = (tmp_path / "composition" / "composition.toml").read_text()
        (tmp_path / "composition" / "composition.toml").write_text(
            composition.replace('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1"]').replace(
                composition[composition.index("[client.operations.get_loan]"):composition.index("[ports.NoticeSender]")], ""
            )
        )

        render_composition_response = rendering.client.render_composition(render_composition_request)

        assert render_composition_response.problems == ()
        assert render_composition_response.removed == ("tests/test_reading_loans_by_loan_id.py",)
        assert not reading.exists()

    def test_a_renamed_term_carries_what_was_written_by_hand_to_the_files_named_for_the_new_term(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text((tree / "compositions" / "library-direct" / f"{name}.toml").read_text())
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(
            composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=(),
        )
        rendering.client.render_composition(render_composition_request)
        loan = tmp_path / "out" / "loans" / "domain" / "loan.py"
        loan.write_text(loan.read_text().replace("import tesser.domain as ts\n", "import tesser.domain as ts\nimport tesser.errors as errors\n").replace(
            "        self._borrower = spec.borrower\n",
            "        if not spec.borrower.strip():\n            raise errors.invalid(\"blank_borrower\", \"a loan needs a borrower\")\n"
            "        self._borrower = spec.borrower\n",
        ))
        reading = tmp_path / "out" / "tests" / "test_reading_loans_by_loan_id.py"
        reading.write_text(reading.read_text().replace('loan_id: str = "loan-1"', 'loan_id: str = "loan-2"'))
        for document in (tmp_path / "composition").iterdir():
            document.write_text(
                document.read_text().replace("Loans", "Rentals").replace("loans", "rentals").replace("Loan", "Rental").replace("loan", "rental")
            )

        render_composition_response = rendering.client.render_composition(render_composition_request)
        check_composition_response = rendering.client.check_composition(
            client.CheckCompositionRequest(composition_dir=str(tmp_path / "composition"), tree_dir=str(tmp_path / "out")),
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "rentals"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert {"loans/domain/loan.py", "tests/test_reading_loans_by_loan_id.py"} <= set(render_composition_response.removed)
        assert render_composition_response.kept == (
            "rentals/domain/rental.py: what was written by hand in loans/domain/loan.py",
            "tests/test_reading_rentals_by_rental_id.py: what was written by hand in tests/test_reading_loans_by_loan_id.py",
        )
        assert 'raise errors.invalid("blank_borrower", "a rental needs a borrower")' in (
            tmp_path / "out" / "rentals" / "domain" / "rental.py").read_text()
        assert 'rental_id: str = "rental-2"' in (tmp_path / "out" / "tests" / "test_reading_rentals_by_rental_id.py").read_text()
        assert not (tmp_path / "out" / "loans").exists()
        assert tested.returncode == 0, tested.stdout
        assert check_composition_response.drifted == ()

    def test_a_client_field_takes_its_type_from_its_own_annotation_or_else_from_a_port_its_steps_call(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("", (
                "\n[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\n"
                "given = \"I have created a loan with POST /loans\"\nwhen = \"I GET /loans/{loan_id}/copies\"\n"
                "then = \"I get back 200 with the copies on the shelf and its shelf_label\"\nroute = \"GET /loans/{loan_id}/copies\"\nstatus = 200\n"
            ))],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[ports.NoticeSender]", (
                    "[client.operations.count_copies]\nrequest = [\"loan_id\"]\nresponse = [\"copies: int\", \"shelf_label\"]\n"
                    "steps = [\"gateway.count_copies\"]\nserves = [\"s-1-c-1\"]\n\n"
                    "[ports.CopyCounter]\noperations.count_copies = { request = [\"loan_id\"], response = [\"copies: int\", \"shelf_label: str\"] }\n\n"
                    "[ports.NoticeSender]"
                )),
            ],
            "implementations.toml": [
                ("[environments.gate]", "[implementations.CopyCounter.shelf]\nclass = \"ShelfCopyCounter\"\nbody = \"agent\"\n\n[environments.gate]"),
                ('LoanRepository = "memory"', 'LoanRepository = "memory", CopyCounter = "shelf"'),
            ],
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]\nshelf_label = ["A1", "B2"]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text + new if old == "" else text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "loans"], cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert "    def __init__(self, copies: int, shelf_label: str) -> None:\n" in (
            tmp_path / "out" / "loans" / "client" / "client.py").read_text()
        assert typed.returncode == 0, typed.stdout

    def test_a_store_lists_every_aggregate_or_those_matching_its_request_and_a_route_answers_them(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("", (
                "\n[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\n"
                "given = \"I have created loans with POST /loans\"\nwhen = \"I GET /loans\"\n"
                "then = \"I get back 200 with the loans, each with its loan_id, borrower and title\"\nroute = \"GET /loans\"\nstatus = 200\n"
                "\n[[jtbds.stories.jtbds]]\nid = \"j-1-d\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-d-1\"\n"
                "given = \"I have created loans with POST /loans\"\nwhen = \"I GET /borrowers/{borrower}/loans\"\n"
                "then = \"I get back 200 with the borrower's loans, each with its loan_id and title\"\n"
                "route = \"GET /borrowers/{borrower}/loans\"\nstatus = 200\n"
            ))],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1", "s-1-d-1"]'),
                ("[ports.NoticeSender]", (
                    "[client.operations.list_loans]\nrequest = []\nresponse = [\"loans\"]\nsteps = [\"repository.list_loans\"]\n"
                    "serves = [\"s-1-c-1\"]\n\n[client.operations.list_borrowed]\nrequest = [\"borrower\"]\n"
                    "response = [\"loans: LoanView[]\"]\nsteps = [\"repository.list_loans_by_borrower\"]\nserves = [\"s-1-d-1\"]\n\n"
                    "[shapes.LoanView]\nloan_id = \"str\"\ntitle = \"str\"\n\n[ports.NoticeSender]"
                )),
                ('operations.load_loan = { request = ["loan_id"], response = ["loan"] }', (
                    'operations.load_loan = { request = ["loan_id"], response = ["loan"] }\n'
                    'operations.list_loans = { request = [], response = ["loans: Loan[]"] }\n'
                    'operations.list_loans_by_borrower = { request = ["borrower"], response = ["loans: Loan[]"] }'
                )),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text + new if old == "" else text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        (tmp_path / "out" / "tests" / "test_listing.py").write_text(
            "import json\nimport urllib.request as urllib_request\n\n\nclass TestListing:\n\n"
            "    def test_every_loan_and_each_borrower_s_loans_are_listed(self, host: str) -> None:\n"
            "        for borrower, title in ((\"Ada\", \"Beloved\"), (\"Grace\", \"Middlemarch\")):\n"
            "            urllib_request.urlopen(urllib_request.Request(f\"{host}/loans\", data=json.dumps({\"borrower\": borrower, \"title\": title}).encode(), "
            "headers={\"Content-Type\": \"application/json\"}, method=\"POST\"), timeout=30)\n"
            "        with urllib_request.urlopen(f\"{host}/loans\", timeout=30) as answer:\n"
            "            listed = json.loads(answer.read())[\"loans\"]\n"
            "        with urllib_request.urlopen(f\"{host}/borrowers/Grace/loans\", timeout=30) as answer:\n"
            "            borrowed = json.loads(answer.read())[\"loans\"]\n"
            "        assert sorted((loan[\"borrower\"], loan[\"title\"]) for loan in listed) == [(\"Ada\", \"Beloved\"), (\"Grace\", \"Middlemarch\")]\n"
            "        assert [loan[\"title\"] for loan in borrowed] == [\"Middlemarch\"]\n"
        )

        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans", "srv", "tests/test_listing.py", "tests/test_reading_loans.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout

    def test_a_store_operation_that_neither_saves_loads_nor_lists_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [(
                'operations.load_loan = { request = ["loan_id"], response = ["loan"] }',
                'operations.load_loan = { request = ["loan_id"], response = ["loan"] }\n'
                'operations.list_loans = { request = ["borrower"], response = ["loan_id"] }',
            )],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "LoanRepository carries loan, so it is a store: one save of it that answers nothing, one load of it by loan_id, and any "
            "number of lists that answer one \"<field>: Loan[]\" and take only fields of its spec to match",
        )

    def test_two_contexts_render_into_one_app_whose_gateway_reaches_the_peer_through_its_client(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "library-catalog"), out_dir=str(tmp_path / "out"), printed=(),
        )
        render_composition_response = rendering.client.render_composition(render_composition_request)
        gateway = tmp_path / "out" / "loans" / "adapters" / "gateways" / "catalog_book_register.py"
        gateway.write_text(gateway.read_text().replace(
            "        return ports.CheckBookResponse()\n",
            "        await self._catalog_client.get_book(catalog_client.GetBookRequest(book_id=check_book_request.book_id))\n"
            "        return ports.CheckBookResponse()\n",
        ))
        (tmp_path / "out" / "tests" / "test_lending_from_the_catalog.py").write_text(
            "import json\nimport urllib.error as urllib_error\nimport urllib.request as urllib_request\n\n\n"
            "class TestLendingFromTheCatalog:\n\n    def test_a_book_is_lent_only_if_it_is_in_the_catalog(self, host: str) -> None:\n"
            "        with urllib_request.urlopen(urllib_request.Request(f\"{host}/books\", data=b'{\"title\": \"Beloved\"}', "
            "headers={\"Content-Type\": \"application/json\"}, method=\"POST\"), timeout=30) as answer:\n"
            "            book_id = json.loads(answer.read())[\"book_id\"]\n"
            "        statuses = []\n"
            "        for book in (book_id, \"nobody\"):\n"
            "            lend = urllib_request.Request(f\"{host}/loans\", data=json.dumps({\"borrower\": \"Ada\", \"book_id\": book}).encode(), "
            "headers={\"Content-Type\": \"application/json\"}, method=\"POST\")\n"
            "            try:\n                with urllib_request.urlopen(lend, timeout=30) as answer:\n                    statuses.append(answer.status)\n"
            "            except urllib_error.HTTPError as error:\n                statuses.append(error.code)\n"
            "        assert statuses == [201, 500]\n"
        )

        again = rendering.client.render_composition(render_composition_request)
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "app", "loans", "catalog", "tests/test_lending_from_the_catalog.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert (render_composition_response.problems, again.problems) == ((), ())
        assert "loans/adapters/gateways/catalog_book_register.py" in again.kept
        assert "            loans_gateways.CatalogBookRegister(self.catalog.client),\n" in (tmp_path / "out" / "app" / "app.py").read_text()
        assert tested.returncode == 0, tested.stdout

    def test_contexts_that_do_not_fit_together_are_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        answered: list[tuple[str, ...]] = []
        for document, old, new, renamed in (
            ("implementations", 'reaches = "catalog"', 'reaches = "patrons"', ""),
            ("implementations", "", "", "composition.patrons"),
            ("composition.catalog", "[ports.BookRepository]",
             "[ports.NoticeSender]\noperations.notify_book = { request = [\"title\"], response = [] }\n\n[ports.BookRepository]", ""),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "library-catalog").glob("*.toml"):
                text = found.read_text()
                if found.stem == document and old:
                    assert old in text
                    text = text.replace(old, new, 1)
                (composition / (f"{renamed}.toml" if renamed and found.stem == "composition.catalog" else found.name)).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ("context loans has a gateway that reaches patrons, and no composition in the directory declares context patrons",),
            ("composition.patrons.toml declares context catalog, and the composition of a further context is named "
             "composition.<context>.toml",),
            ("contexts loans and catalog both declare port NoticeSender, and implementations.toml names a port once, "
             "so one context declares it",),
        ]
        assert not (tmp_path / "out").exists()

    def test_a_story_file_that_still_has_reached_by_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('route = "GET /loans/{loan_id}"', 'route = "GET /loans/{loan_id}"\nreached_by = [{ route = "POST /loans" }]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "s-1-b-1 has reached_by, which is no longer part of the story format; write in its given how it is "
            "reached, and write the calls in its root test",
        )

    def test_two_ports_declaring_one_operation_name_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [(
                'operations.send_notice = { request = ["borrower", "title"], response = [] }',
                'operations.send_notice = { request = ["borrower", "title"], response = [] }\n'
                'operations.issue_loan_id = { request = [], response = ["loan_id"] }',
            )],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "ports NoticeSender and LoanIdentityRepository both declare issue_loan_id, and ports exports one "
            "IssueLoanIdRequest and one IssueLoanIdResponse, so one port declares it",
        )

    def test_an_action_that_builds_something_other_than_the_aggregate_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [('builds = "Loan"', 'builds = "Book"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "actions.loan.operations.record_loan builds 'Book', and the one aggregate it can build is 'Loan'",
        )

    def test_two_client_operations_on_one_route_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}\"\nthen = \"I get back 200 with its title\"\nroute = \"GET /loans/{loan_id}\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.get_title]\nrequest = [\"loan_id\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "client operations get_loan and get_title are both GET /loans/{loan_id}, and HTTP reaches only one of them",
        )

    def test_an_integer_path_parameter_reaches_the_client_as_an_integer(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}/copies/{copies}\"\nthen = \"I get back 200 with its loan_id\"\nroute = \"GET /loans/{loan_id}/copies/{copies}\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('[aggregate.spec]\nloan_id = "str"', '[aggregate.spec]\ncopies = "int"\nloan_id = "str"'),
                ('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\ncopies = "int"\nloan_id = "str"'),
                ('request = ["borrower", "title"]\nresponse = ["loan_id"]', 'request = ["borrower", "title", "copies"]\nresponse = ["loan_id"]'),
                ('response = ["loan_id", "borrower", "title"]', 'response = ["loan_id", "borrower", "title", "copies"]'),
                ('[orchestrator.operations.arrange_loan]\nrequest = ["loan_id", "borrower", "title"]', '[orchestrator.operations.arrange_loan]\nrequest = ["loan_id", "borrower", "title", "copies"]'),
                ('[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title"]', '[actions.loan.operations.record_loan]\nbuilds = "Loan"\ncalls = "save_loan"\nrequest = ["loan_id", "borrower", "title", "copies"]'),
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.check_copies]\nrequest = [\"loan_id\", \"copies\"]\nresponse = [\"loan_id\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        probe = (
            "import asyncio\n"
            "import loans.adapters.handlers as handlers\n"
            "import loans.adapters.handlers.test_http as test_http\n"
            "import protocol\n"
            "fake = test_http.FakeLoansClient()\n"
            "asyncio.run(handlers.HttpHandler(fake).check_copies("
            "protocol.HttpRequest(path_params={'loan_id': 'loan-1', 'copies': '2'}, body=b'')))\n"
            "print(repr(fake.check_copies_requests[0].copies))\n"
        )

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}
        probed = subprocess.run([sys.executable, "-c", probe], cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env)
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/adapters/handlers", "protocol"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )

        assert render_composition_response.problems == ()
        assert (probed.stdout, probed.stderr) == ("2\n", "")
        assert tested.returncode == 0, tested.stdout

    def test_a_command_that_takes_nothing_renders_a_spec_that_parses(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "composition.toml": [
                ("[aggregate.reads]", "[aggregate.commands.close_loan]\ntakes = {}\noutcomes = [\"closed\"]\n\n[aggregate.reads]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        domain_module = (tmp_path / "out" / "loans" / "domain" / "loan.py").read_text()

        assert render_composition_response.problems == ()
        assert ast.parse(domain_module)
        assert "class CloseLoanSpec(ts.Spec):" in domain_module

    def test_two_routes_differing_only_by_a_path_parameter_render_two_root_tests(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans\"\nthen = \"I get back 200 with a loan_id\"\nroute = \"GET /loans\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.list_loans]\nrequest = [\"loan_id\"]\nresponse = [\"loan_id\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert sorted(path.name for path in (tmp_path / "out" / "tests").glob("test_*.py")) == [
            "test_reading_loans.py", "test_reading_loans_by_loan_id.py", "test_submitting_loans.py",
        ]

    def test_a_rendered_tree_collects_its_root_tests_by_default(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        testpaths = [line for line in (tmp_path / "out" / "pyproject.toml").read_text().splitlines() if line.startswith("testpaths")]
        assert len(testpaths) == 1
        assert '"tests"' in testpaths[0]

    def test_a_path_naming_one_parameter_twice_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}/title/{loan_id}\"\nthen = \"I get back 200 with its title\"\nroute = \"GET /loans/{loan_id}/title/{loan_id}\"\nstatus = 200\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.get_title]\nrequest = [\"loan_id\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "/loans/{loan_id}/title/{loan_id} names {loan_id} more than once, and a path parameter is bound once",
        )

    def test_a_path_parameter_that_is_not_an_integer_answers_400_never_a_crash(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text((tree / "compositions" / "library" / f"{name}.toml").read_text())
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        probe = (
            "import protocol\n"
            "for text in ['--2', '-', '', '+2', '1_0', '2 ', '\\u0663', '9' * 5000, '2', '-7']:\n"
            "    try:\n"
            "        answer = repr(protocol.HttpRequest(path_params={'copies': text}, body=b'').integer_path_param('copies'))\n"
            "    except protocol.BadRequest:\n"
            "        answer = 'bad request'\n"
            "    except Exception as error:\n"
            "        answer = type(error).__name__\n"
            "    print(answer)\n"
        )

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}
        probed = subprocess.run([sys.executable, "-c", probe], cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env)

        assert render_composition_response.problems == ()
        assert (probed.stdout.splitlines(), probed.stderr) == (["bad request"] * 8 + ["2", "-7"], "")

    def test_an_empty_sample_list_is_a_problem_not_a_crash(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"generator.toml": [('borrower = ["Ada", "Grace"]', "borrower = []")]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("generator.toml lists no sample values for borrower",)

    def test_an_enum_value_no_story_names_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["lapsed"]\n\n[aggregate.reads]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("enum LoanState value lapsed is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",)

    def test_a_client_request_and_response_field_no_story_names_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\nloan_id = "str"\nshelf = "str"'), ('request = ["borrower", "title"]\nresponse = ["loan_id"]\nsteps = ["identity', 'request = ["borrower", "title", "shelf"]\nresponse = ["loan_id"]\nsteps = ["identity'), ('response = ["loan_id", "borrower", "title"]\nsteps = ["repository.load_loan"]', 'response = ["loan_id", "borrower", "title", "shelf"]\nsteps = ["repository.load_loan"]')],
            'generator.toml': [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\nshelf = ["A1", "B2"]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "client operation lend_book request field shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition",
            "client operation get_loan response field shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition",
            "aggregate read shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition",
        )

    def test_an_aggregate_read_no_story_names_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\nloan_id = "str"\nshelf = "str"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("aggregate read shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

    def test_a_signal_payload_field_no_story_names_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\nloan_id = "str"\nshelf = "str"'), ('payload = ["loan_id"]', 'payload = ["loan_id", "shelf"]')],
            'generator.toml': [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\nshelf = ["A1", "B2"]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert "signal return_book payload field shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition" in render_composition_response.problems

    def test_a_command_outcome_no_story_names_is_a_problem_but_the_first_is_the_success_outcome(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[aggregate.commands.renew_loan]\ntakes = {}\noutcomes = ["renewed", "refused"]\n\n[aggregate.reads]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("command renew_loan outcome refused is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

    def test_every_untraced_piece_is_reported_in_one_render(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["lapsed", "open"]\n\n[aggregate.commands.renew_loan]\ntakes = {}\noutcomes = ["renewed", "refused"]\n\n[aggregate.reads]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "enum LoanState value lapsed is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",
            "enum LoanState value open is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",
            "command renew_loan outcome refused is named by no story: write it in a story's given, when, or then, or remove it from the composition",
        )

    def test_a_name_matches_a_story_as_a_whole_token_with_spaces_for_underscores_in_any_case(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["lapsed_loan", "loan_i"]\n\n[aggregate.reads]')],
            'story.toml': [('then = "the loan is on record and I can read it back"', 'then = "the loan is on record and I can read it back, even a Lapsed Loan"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("enum LoanState value loan_i is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",)

    def test_an_enum_value_a_language_term_defines_needs_no_story(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["overdue_notice", "lapsed"]\n\n[aggregate.reads]')],
            'language.toml': [('[[terms]]\nterm = "borrower"', '[[terms]]\nterm = "overdue notice"\nmeans = "The notice a borrower gets when a loan runs past its due date."\n\n[[terms]]\nterm = "borrower"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("enum LoanState value lapsed is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",)

    def test_an_enum_value_a_language_code_name_defines_needs_no_story(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["notice_sender"]\n\n[aggregate.reads]')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()

    def test_an_enum_value_a_story_names_needs_no_language_term(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["lapsed"]\n\n[aggregate.reads]')],
            'story.toml': [('then = "the loan is on record and I can read it back"', 'then = "the loan is on record and I can read it back, even once lapsed"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()

    def test_a_language_term_does_not_trace_a_piece_that_is_not_an_enum_value(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]\nloan_id = "str"', '[aggregate.reads]\nloan_id = "str"\nshelf = "str"')],
            'language.toml': [('[[terms]]\nterm = "borrower"', '[[terms]]\nterm = "shelf"\nmeans = "Where a lent book is kept when it is not lent."\n\n[[terms]]\nterm = "borrower"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("aggregate read shelf is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

    def test_the_scope_out_list_does_not_name_a_piece_for_a_story(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[enums]\nLoanState = ["lapsed"]\n\n[aggregate.reads]')],
            'story.toml': [('[[jtbds]]\nid = "j-root"', '[scope]\nout = ["lapsed loans"]\n\n[[jtbds]]\nid = "j-root"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ("enum LoanState value lapsed is named by no story and is no term in language.toml: write it in a story's given, when, or then, define it as a term in language.toml, or remove it from the composition",)

    def test_a_domain_stub_answers_the_first_listed_outcome_which_is_the_success_outcome(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[aggregate.commands.renew_loan]\ntakes = { title = "str" }\noutcomes = ["renewed", "refused"]\n\n[aggregate.reads]'), ('builds = "Loan"\ncalls = "save_loan"', 'builds = "Loan"\ncommands = ["renew_loan"]\ncalls_on = ["renewed"]\ncalls = "save_loan"')],
            'story.toml': [('then = "', 'then = "a renewal can be refused, and ')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        domain_modules = [path for path in (tmp_path / "out").rglob("domain/loan.py")]
        assert len(domain_modules) == 1
        assert "return RenewLoanOutcome.RENEWED" in domain_modules[0].read_text()

    def test_a_command_with_one_outcome_renders_with_its_action_matching_that_one_outcome(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            'composition.toml': [('[aggregate.reads]', '[aggregate.commands.renew_loan]\ntakes = { title = "str" }\noutcomes = ["renewed"]\n\n[aggregate.reads]'), ('builds = "Loan"\ncalls = "save_loan"', 'builds = "Loan"\ncommands = ["renew_loan"]\ncalls_on = ["renewed"]\ncalls = "save_loan"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()

    def test_a_composition_with_no_engine_renders_a_service_that_calls_its_ports_and_no_engine_piece(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "library-direct"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "app", "loans", "protocol", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "app", "loans", "protocol", "srv", "tests", "conftest.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        served = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        rendered = {
            path.relative_to(tmp_path / "out").as_posix(): path.read_text()
            for path in (tmp_path / "out").rglob("*")
            if path.is_file() and path.name != ".tesser-rendered" and "__pycache__" not in path.parts and ".mypy_cache" not in path.parts
        }
        assert [path for path, text in rendered.items() if "restate" in text.lower() or "engine" in text.lower()] == []
        assert [path for path in rendered if {"activities", "workflows", "dispatchers", "orchestrators", "relays"} & set(path.split("/")[:-1])] == []
        assert "loans/application/client/__init__.py" not in rendered
        assert "        await self._notice_sender.send_notice(MapToSendNoticeRequest(lend_book_request))\n" in rendered[
            "loans/application/loan_service.py"]
        assert "1 failed, 1 passed" in served.stdout, served.stdout
        assert "FAILED tests/test_reading_loans_by_loan_id.py::TestReadingLoansByLoanId::test_s_1_b_1" in served.stdout
        assert "assert 422 == 200" in served.stdout

    def test_a_workflow_without_an_engine_is_a_problem_for_each_piece_that_needs_one(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "infra.toml": [('[engine.restate]\nbody = "supported"\nengine_path = "/restate"\nengine_url_variable = "RESTATE_URL"\n\n', "")],
            "implementations.toml": [('engine = "restate"\n', "")],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "composition.toml declares [orchestrator], which runs on a durable-execution engine, and infra.toml declares no "
            "[engine]: without one, a client operation's steps call its ports directly",
            "composition.toml declares [actions], which runs on a durable-execution engine, and infra.toml declares no "
            "[engine]: without one, a client operation's steps call its ports directly",
            "composition.toml declares [signals], which runs on a durable-execution engine, and infra.toml declares no "
            "[engine]: without one, a client operation's steps call its ports directly",
            "step orchestrator.start_arrange_loan runs the orchestrator, and infra.toml declares no [engine] to run it: without "
            "one, a client operation's steps call its ports directly",
        )
        assert not (tmp_path / "out").exists()

    def test_an_environment_running_an_engine_infra_toml_does_not_declare_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {"implementations.toml": [('hosts = ["http"]', 'engine = "restate"\nhosts = ["http"]')]}
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == (
            "environment gate runs the restate engine, and infra.toml declares no [engine]",
        )

    def test_an_app_with_no_engine_and_nothing_to_configure_renders_a_config_that_takes_nothing(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[implementations.LoanIdentityRepository.uuid]\nbody = \"supported\"",
                "[implementations.LoanIdentityRepository.handwritten]\nclass = \"HandwrittenLoanIdentityRepository\"\nbody = \"agent\"",
            ), ('LoanIdentityRepository = "uuid"', 'LoanIdentityRepository = "handwritten"')],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "app", "loans", "protocol", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "app", "loans", "protocol", "srv", "tests", "conftest.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        assert "    def __init__(\n        self\n    ) -> None:\n        pass\n" in (tmp_path / "out" / "loans" / "component" / "component.py").read_text()

    def test_an_app_with_no_engine_reads_and_passes_its_store_location(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "implementations.toml": [(
                "[implementations.LoanRepository.memory]\nbody = \"supported\"",
                "[implementations.LoanRepository.sqlite]\nclass = \"SqliteLoanRepository\"\nbody = \"agent\"",
            ), ('LoanRepository = "memory"', 'LoanRepository = "sqlite"')],
            "infra.toml": [("[storage.memory]", "[storage.sqlite]\nlocation_variable = \"LOAN_DB_PATH\"")],
        }
        for name in ("language", "story", "infra", "composition", "implementations", "generator"):
            text = (tree / "compositions" / "library-direct" / f"{name}.toml").read_text()
            for old, new in edits.get(f"{name}.toml", []):
                assert old in text
                text = text.replace(old, new, 1)
            (tmp_path / "composition").mkdir(exist_ok=True)
            (tmp_path / "composition" / f"{name}.toml").write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "composition"), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "app", "loans", "protocol", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "app", "loans", "protocol", "srv", "tests", "conftest.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        assert '"LOAN_DB_PATH": str(locations / "sqlite_location"),' in (tmp_path / "out" / "conftest.py").read_text()

    def test_a_refusal_renders_its_match_where_the_aggregate_is_built_and_a_service_test_that_it_refuses(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "voyages/application"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        service = (tmp_path / "out" / "voyages" / "application" / "voyage_service.py").read_text()
        assert (
            "    def __init__(self, plan_voyage_request: client.PlanVoyageRequest, look_up_harbor_response: ports.LookUpHarborResponse, "
            "issue_voyage_id_response: ports.IssueVoyageIdResponse) -> None:\n"
            "        match look_up_harbor_response.outcome:\n"
            "            case ports.LookUpHarborOutcome.UNCHARTED:\n"
            "                raise errors.invalid(\"uncharted_harbor\", \"a voyage is planned to a charted harbor\", field=\"harbor\")\n"
            "            case ports.LookUpHarborOutcome.CHARTED:\n"
            "                pass\n"
            "            case _ as never:\n"
            "                typing.assert_never(never)\n"
        ) in service
        service_test = (tmp_path / "out" / "voyages" / "application" / "test_voyage_service.py").read_text()
        assert "class FakeHarborChartAnsweringUncharted(ports.HarborChart):" in service_test
        assert "    async def test_plan_voyage_refuses_uncharted_harbor(self) -> None:" in service_test
        assert "    async def test_get_voyage_refuses_an_unknown_voyage(self) -> None:" in service_test

    def test_an_enum_a_port_answers_renders_as_the_responses_outcome_declared_in_the_ports_module(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))

        assert render_composition_response.problems == ()
        port = (tmp_path / "out" / "voyages" / "application" / "ports" / "harbor_chart.py").read_text()
        assert (
            "class LookUpHarborOutcome(enum.Enum):\n"
            "    UNCHARTED = \"uncharted\"\n"
            "    CHARTED = \"charted\"\n"
        ) in port
        assert (
            "    def __init__(self, harbor_name: str, outcome: LookUpHarborOutcome) -> None:\n"
            "        self.harbor_name = harbor_name\n"
            "        self.outcome = outcome\n"
        ) in port
        assert "harbor_standing" not in port
        assert "HarborStanding" not in (tmp_path / "out" / "voyages" / "domain" / "voyage.py").read_text()
        assert ("from voyages.application.ports.harbor_chart import LookUpHarborOutcome as LookUpHarborOutcome"
                in (tmp_path / "out" / "voyages" / "application" / "ports" / "__init__.py").read_text())

    def test_a_port_answering_two_enums_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        composition = tmp_path / "composition"
        composition.mkdir()
        for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
            text = found.read_text()
            if found.name == "composition.toml":
                old = '"harbor_standing: HarborStanding"]'
                assert old in text
                text = text.replace(old, '"harbor_standing: HarborStanding", "harbor_depth: HarborStanding"]', 1)
            (composition / found.name).write_text(text)

        problems = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
        )).problems

        assert problems == (
            "ports.HarborChart operation look_up_harbor answers 2 enums (harbor_standing, harbor_depth); a response carries at "
            "most one outcome, because its caller matches one answer: answer one, or split the operation",
        )
        assert not (tmp_path / "out").exists()

    def test_a_refusal_that_cannot_be_raised_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        refusal = 'refuses = [{ code = "uncharted_harbor", when = "harbor_standing", is = "uncharted", message = "a voyage is planned to a charted harbor", field = "harbor" }]'
        answered: list[tuple[str, ...]] = []
        for old, new in (
            (refusal, 'refuses = [{ code = "uncharted_harbor", when = "harbor_depth", is = "uncharted" }]'),
            (refusal, 'refuses = [{ code = "uncharted_harbor", when = "harbor_standing", is = "sunk" }]'),
            (refusal, 'refuses = [{ code = "uncharted_harbor", when = "harbor_name", is = "uncharted" }]'),
            ('steps = ["gateway.look_up_harbor", "identity.issue_voyage_id", "repository.save_voyage"]',
             'steps = ["identity.issue_voyage_id", "repository.save_voyage", "gateway.look_up_harbor"]'),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == "composition.toml":
                    assert old in text
                    text = text.replace(old, new, 1)
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ("client operation plan_voyage refuses uncharted_harbor when harbor_depth is answered, and none of its steps answers harbor_depth",),
            ("client operation plan_voyage refuses uncharted_harbor when harbor_standing is sunk, which HarborStanding does not list",),
            ("client operation plan_voyage refuses uncharted_harbor when harbor_name is uncharted, and gateway.look_up_harbor answers "
             "harbor_name as str, not an enum: a refusal matches an enum field a step answers",),
            ("client operation plan_voyage refuses on harbor_standing, and no step after the one that answers it builds the voyage, "
             "where a refusal is raised: put that step before the step that builds or loads the voyage",),
        ]
        assert not (tmp_path / "out").exists()

    def test_a_fake_and_a_gateway_stub_answer_the_enum_member_no_refusal_names_whatever_the_order(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        composition = tmp_path / "composition"
        composition.mkdir()
        for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
            text = found.read_text()
            if found.name == "implementations.toml":
                text = text[:text.index("[implementations.HarborChart.harbors.operations.look_up_harbor]")] + \
                    text[text.index("[implementations.HarborRepository.memory]"):]
            (composition / found.name).write_text(text)
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=())
        )
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "voyages", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert 'return ports.LookUpHarborResponse(harbor_name="Hobart", outcome=ports.LookUpHarborOutcome.CHARTED)' in (
            tmp_path / "out" / "voyages" / "application" / "test_voyage_service.py").read_text()
        assert '        return ports.LookUpHarborResponse(harbor_name="", outcome=ports.LookUpHarborOutcome.CHARTED)\n' in (
            tmp_path / "out" / "voyages" / "adapters" / "gateways" / "harbors_harbor_chart.py").read_text()

    def test_a_gateway_that_says_what_it_calls_renders_the_call_to_the_peer_and_tests_both_answers(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "voyages/adapters/gateways", "harbors/application"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        gateway = (tmp_path / "out" / "voyages" / "adapters" / "gateways" / "harbors_harbor_chart.py").read_text()
        assert (
            "        try:\n"
            "            get_harbor_response = await self._harbors_client.get_harbor(harbors_client.GetHarborRequest(harbor_id=look_up_harbor_request.harbor))\n"
            "        except harbors_client.HarborRejected:\n"
            "            return ports.LookUpHarborResponse(harbor_name=\"\", outcome=ports.LookUpHarborOutcome.UNCHARTED)\n"
            "        return ports.LookUpHarborResponse(harbor_name=get_harbor_response.place_name, outcome=ports.LookUpHarborOutcome.CHARTED)\n"
        ) in gateway
        gateway_test = (tmp_path / "out" / "voyages" / "adapters" / "gateways" / "test_harbors_harbor_chart.py").read_text()
        assert "class FakeRejectingHarborsClient(harbors_client.HarborsClient):" in gateway_test
        assert "    async def test_look_up_harbor_answers_its_refused_members_when_harbors_refuses(self) -> None:" in gateway_test
        assert ('raise client.HarborRejected("unknown_harbor", "no harbor has that harbor_id") from unknown'
                in (tmp_path / "out" / "harbors" / "application" / "harbor_service.py").read_text())

    def test_a_gateway_call_the_peer_cannot_answer_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        answered: list[tuple[str, ...]] = []
        for old, new in (
            ('calls = "get_harbor"', 'calls = "find_harbor"'),
            ('sends = { harbor_id = "harbor" }', 'sends = { harbor_id = "port" }'),
            ('answers = { harbor_name = "place_name", harbor_standing = "charted" }', 'answers = { harbor_standing = "charted" }'),
            ('refused = { harbor_standing = "uncharted" }', 'refused = { harbor_standing = "sunk" }'),
            ('reaches = "harbors"\n', ''),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == "implementations.toml":
                    assert old in text
                    text = text.replace(old, new, 1)
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        at = "[implementations.HarborChart.harbors.operations.look_up_harbor]"
        assert answered == [
            (f"{at} calls find_harbor, which context harbors's client does not declare",),
            (f"{at} sends harbors's harbor_id from port, which look_up_harbor does not take: say sends = "
             "{ harbor_id = \"<a field look_up_harbor takes>\" }",),
            (f"{at} answers harbor_name, a str, from harbors's harbor_name, which get_harbor does not answer as a str: say answers = "
             "{ harbor_name = \"<a field get_harbor answers>\" }, or leave out this operation's calls and write the call by hand",),
            (f"{at} refused harbor_standing as sunk, which HarborStanding does not list",),
            ("[implementations.HarborChart.harbors] says which operations it calls and reaches no context: a gateway that calls "
             "another context's client says reaches = \"<context>\"",),
        ]

    def test_the_host_test_issues_what_a_step_reads_from_another_context_before_it_calls_the_route(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        host_test = (tmp_path / "out" / "srv" / "http" / "test_main.py").read_text()
        assert "            (\"POST\", \"/harbors\", b'{\"place_name\": \"Valparaiso\"}', {}),\n" in host_test
        assert "            (\"GET\", \"/harbors/-1\", None, {}),\n" in host_test
        assert "            (\"POST\", \"/voyages\", b'{\"vessel\": \"Endeavour\", \"harbor\": 1}', {\"harbor\": \"harbor_id\"}),\n" in host_test
        assert "        assert answers == [400, 201, 422, 400, 201, 422, 422]\n" in host_test

    def test_a_root_test_takes_a_fixture_that_issues_what_its_route_looks_up_in_another_context(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_submitting_voyages.py", "tests/test_submitting_harbors.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert (
            "@pytest.fixture\n"
            "def issued_harbor_id(host: str) -> int:\n"
            "    answer = httpx.post(f\"{host}/harbors\", json={\"place_name\": \"Valparaiso\"}, timeout=DEADLINE_SECONDS)\n"
            "    answer.raise_for_status()\n"
            "    return int(answer.json()[\"harbor_id\"])\n"
        ) in (tmp_path / "out" / "conftest.py").read_text()
        submitting = (tmp_path / "out" / "tests" / "test_submitting_voyages.py").read_text()
        assert "import json\n" in submitting
        assert "    def test_s_1_a_1(self, host: str, issued_harbor_id: int) -> None:\n" in submitting
        assert 'f"{host}/voyages", data=json.dumps({"vessel": "Endeavour", "harbor": issued_harbor_id}).encode(),' in submitting
        reading = (tmp_path / "out" / "tests" / "test_reading_voyages_by_voyage_id.py").read_text()
        assert "    def test_s_1_b_1(self, host: str) -> None:\n" in reading
        assert "import json" not in reading
        assert "issued_" not in (tmp_path / "out" / "tests" / "test_submitting_harbors.py").read_text()

    def test_a_render_names_each_root_test_written_by_hand_that_calls_the_route_without_the_fixture(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        )
        rendering.client.render_composition(render_composition_request)
        reading = tmp_path / "out" / "tests" / "test_reading_voyages_by_voyage_id.py"
        reading.write_text(reading.read_text().replace(
            "    def test_s_1_b_1(self, host: str) -> None:\n        voyage_id: str = \"voyage-1\"\n",
            "    def test_s_1_b_1(self, host: str) -> None:\n"
            "        planning = urllib_request.Request(\n"
            "            f\"{host}/voyages\", data=b'{\"vessel\": \"Endeavour\", \"harbor\": 1}', "
            "headers={\"Content-Type\": \"application/json\"}, method=\"POST\"\n"
            "        )\n"
            "        with urllib_request.urlopen(planning, timeout=30) as planned:\n"
            "            voyage_id: str = planned.headers[\"Location\"]\n"
            "\n"
            "    def test_s_2(self, host: str, issued_harbor_id: int) -> None:\n"
            "        planning = urllib_request.Request(\n"
            "            f\"{host}/voyages\", data=str(issued_harbor_id).encode(), headers={\"Content-Type\": \"application/json\"}, method=\"POST\"\n"
            "        )\n"
            "\n"
            "    def test_s_3(self, host: str) -> None:\n"
            "        charting = urllib_request.Request(f\"{host}/harbors\", data=b'{}', method=\"POST\")\n"
            "        voyage_id: str = \"voyage-1\"\n",
        ))

        render_composition_response = rendering.client.render_composition(render_composition_request)

        assert render_composition_response.problems == ()
        assert [kept for kept in render_composition_response.kept if "issued_harbor_id" in kept] == [
            "tests/test_reading_voyages_by_voyage_id.py: TestReadingVoyagesByVoyageId.test_s_1_b_1, written by hand, calls POST "
            "/voyages and does not take the issued_harbor_id fixture: take it, and send it as harbor, which POST /voyages looks "
            "up in another context",
        ]

    def test_a_new_aggregate_starts_with_its_initial_value_and_a_step_applies_a_command_to_the_one_it_loads(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "voyages"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        service = (tmp_path / "out" / "voyages" / "application" / "voyage_service.py").read_text()
        assert "            stage=domain.VoyageStage.PLANNED,\n" in service
        assert "            stage=domain.VoyageStage(load_voyage_response.voyage.stage),\n" in service
        assert (
            "        try:\n"
            "            match voyage.depart_voyage(domain.DepartVoyageSpec()):\n"
            "                case domain.DepartVoyageOutcome.DEPARTED:\n"
            "                    pass\n"
            "                case domain.DepartVoyageOutcome.ALREADY_DEPARTED:\n"
            "                    raise client.VoyageRejected(\"already_departed\", \"already departed\")\n"
            "                case _ as never:\n"
            "                    typing.assert_never(never)\n"
            "        except errors.DomainError as domain_error:\n"
            "            raise client.VoyageRejected(domain_error.code, domain_error.message) from domain_error\n"
            "        async with self._voyage_store.transaction() as voyage_repository:\n"
            "            await voyage_repository.save_voyage(MapToSaveVoyageRequest(voyage))\n"
        ) in service
        stub = (tmp_path / "out" / "voyages" / "domain" / "voyage.py").read_text()
        assert "        self._stage = spec.stage\n" in stub
        assert "        return Text(self._stage.value)\n" in stub
        service_test = (tmp_path / "out" / "voyages" / "application" / "test_voyage_service.py").read_text()
        assert '        assert depart_voyage_response.stage in ("planned", "departed")\n' in service_test

    def test_an_initial_value_or_a_command_step_that_cannot_be_rendered_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        departing = 'steps = ["repository.load_voyage", "aggregate.depart_voyage", "repository.save_voyage"]'
        answered: list[tuple[str, ...]] = []
        for old, new in (
            ('[aggregate.initial]\nstage = "planned"', '[aggregate.initial]\nstage = "sunk"'),
            ('[aggregate.initial]\nstage = "planned"', '[aggregate.initial]\nberth = "planned"'),
            (departing, 'steps = ["aggregate.depart_voyage", "repository.load_voyage", "repository.save_voyage"]'),
            (departing, 'steps = ["repository.load_voyage", "aggregate.depart_voyage", "aggregate.depart_voyage", "repository.save_voyage"]'),
            (departing, 'steps = ["repository.load_voyage", "aggregate.dock_voyage", "repository.save_voyage"]'),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == "composition.toml":
                    assert old in text
                    text = text.replace(old, new, 1)
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ("[aggregate.initial] starts stage as 'sunk', and stage is a VoyageStage: write one of planned, departed",),
            ("[aggregate.initial] names berth, which [aggregate.spec] does not hold: an initial value is what a spec field of a "
             "new Voyage starts as",),
            ("step aggregate.depart_voyage applies depart_voyage to the voyage, and no step before it builds or loads one: put it "
             "after the step that loads the voyage",),
            ("client operation depart_voyage applies two commands, and a service method decides once: apply one, or make one "
             "command of the two",),
            ("step aggregate.dock_voyage names dock_voyage, which [aggregate.commands] does not declare",),
        ]
        assert not (tmp_path / "out").exists()

    def test_an_int_identity_crosses_every_layer_as_an_int_and_the_tests_sample_it_as_one(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "harbors", "srv"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "harbors", "voyages", "srv", "tests", "conftest.py"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        out = tmp_path / "out" / "harbors"
        assert "    def identity(self) -> int:\n" in (out / "domain" / "harbor.py").read_text()
        assert "        self._harbors: dict[int, ports.Harbor] = {}\n" in (out / "adapters" / "repositories" / "memory_harbor_repository.py").read_text()
        assert "    def __init__(self, harbor_id: int) -> None:\n" in (out / "client" / "client.py").read_text()
        assert 'harbor_id=http_request.integer_path_param("harbor_id"),' in (out / "adapters" / "handlers" / "http.py").read_text()
        assert "        fake_harbor_store.harbors[1] = ports.Harbor(harbor_id=1, place_name=\"Valparaiso\")\n" in (
            out / "application" / "test_harbor_service.py").read_text()
        assert "        harbor_id: int = 1\n" in (tmp_path / "out" / "tests" / "test_reading_harbors_by_harbor_id.py").read_text()

    def test_an_int_identity_a_uuid_issues_or_a_sample_of_another_type_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        answered: list[tuple[str, ...]] = []
        for name, old, new in (
            ("implementations.toml", 'HarborIdentityRepository = "ledger"', 'HarborIdentityRepository = "uuid"'),
            ("generator.toml", "harbor_id = [1, 2]", 'harbor_id = ["harbor-1", "harbor-2"]'),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == name:
                    assert old in text
                    text = text.replace(old, new, 1)
                if found.name == "implementations.toml":
                    text += "\n[implementations.HarborIdentityRepository.uuid]\nbody = \"supported\"\n"
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ('HarborIdentityRepository is uuid, which issues text, and IssueHarborIdResponse answers harbor_id as an int: '
             'implement it with body = "agent"',),
            ('generator.toml samples harbor_id as "harbor-1", and harbor_id is a int there: write a sample that is a int',),
        ]

    def test_a_draft_identity_builds_a_draft_before_the_identity_is_issued(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))

        assert render_composition_response.problems == ()
        service = (tmp_path / "out" / "harbors" / "application" / "harbor_service.py").read_text()
        assert (
            "    async def chart_harbor(self, chart_harbor_request: client.ChartHarborRequest) -> client.ChartHarborResponse:\n"
            "        try:\n"
            "            domain.Harbor(MapToDraftHarborSpec(chart_harbor_request))\n"
            "        except errors.DomainError as domain_error:\n"
            "            raise client.HarborRejected(domain_error.code, domain_error.message) from domain_error\n"
            "        issue_harbor_id_response = await self._harbor_identity_repository.issue_harbor_id(ports.IssueHarborIdRequest())\n"
        ) in service
        assert "            harbor_id=0,\n" in service

    def test_a_draft_identity_of_another_type_or_before_what_the_draft_needs_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        answered: list[tuple[str, ...]] = []
        for name, old, new in (
            ("composition.harbors.toml", "draft_identity = 0", 'draft_identity = "draft"'),
            ("composition.toml", 'identity = "voyage_id"\n', 'identity = "voyage_id"\ndraft_identity = "draft"\n'),
        ):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == name:
                    assert old in text
                    text = text.replace(old, new, 1)
                if found.name == "composition.toml" and name == "composition.toml":
                    text = text.replace('steps = ["gateway.look_up_harbor", "identity.issue_voyage_id", "repository.save_voyage"]',
                                        'steps = ["identity.issue_voyage_id", "gateway.look_up_harbor", "repository.save_voyage"]', 1)
                    text = text.replace('stage = "VoyageStage"\n', 'stage = "VoyageStage"\nharbor_name = "str"\n')
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ("[aggregate] draft_identity is 'draft', and the identity harbor_id is a int: write a int the domain accepts as an "
             "identity",),
            ("MapToDraftVoyageSpec needs harbor_name, and nothing before it in the steps holds one: with a draft_identity, client "
             "operation plan_voyage builds a draft voyage before identity.issue_voyage_id issues its voyage_id, from what the steps "
             "before identity.issue_voyage_id hold, so put the steps that answer it before identity.issue_voyage_id",),
        ]

    def test_a_request_field_an_operation_checks_is_made_into_its_domain_value_before_any_step(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(client.RenderCompositionRequest(
            composition_dir=str(tree / "compositions" / "voyages-harbors"), out_dir=str(tmp_path / "out"), printed=(),
        ))

        assert render_composition_response.problems == ()
        out = tmp_path / "out" / "voyages" / "domain"
        assert (
            "    async def plan_voyage(self, plan_voyage_request: client.PlanVoyageRequest) -> client.PlanVoyageResponse:\n"
            "        try:\n"
            "            domain.Vessel(plan_voyage_request.vessel)\n"
            "        except errors.DomainError as domain_error:\n"
            "            raise client.VoyageRejected(domain_error.code, domain_error.message) from domain_error\n"
            "        look_up_harbor_response = await self._harbor_chart.look_up_harbor(MapToLookUpHarborRequest(plan_voyage_request))\n"
        ) in (tmp_path / "out" / "voyages" / "application" / "voyage_service.py").read_text()
        assert (
            "class Vessel(ts.ValueObject):\n"
            "\n"
            "    _value: str\n"
            "\n"
            "    def __init__(self, value: str) -> None:\n"
            "        object.__setattr__(self, \"_value\", value)\n"
            "\n"
            "    def __str__(self) -> str:\n"
            "        return serialization.canonical_str(self._value)\n"
        ) in (out / "voyage.py").read_text()
        assert "from voyages.domain.voyage import Vessel as Vessel\n" in (out / "__init__.py").read_text()
        assert '        vessel = domain.Vessel("Endeavour")\n' in (out / "test_voyage.py").read_text()

    def test_a_check_on_a_field_the_request_lacks_or_with_a_name_the_domain_holds_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        answered: list[tuple[str, ...]] = []
        for new in ('checks = { berth = "Berth" }', 'checks = { vessel = "Voyage" }', 'checks = { harbor = "Vessel", vessel = "Vessel" }'):
            composition = tmp_path / str(len(answered))
            composition.mkdir()
            for found in (tree / "compositions" / "voyages-harbors").glob("*.toml"):
                text = found.read_text()
                if found.name == "composition.toml":
                    assert 'checks = { vessel = "Vessel" }' in text
                    text = text.replace('checks = { vessel = "Vessel" }', new, 1)
                (composition / found.name).write_text(text)
            answered.append(rendering.client.render_composition(client.RenderCompositionRequest(
                composition_dir=str(composition), out_dir=str(tmp_path / "out"), printed=(),
            )).problems)

        assert answered == [
            ("client operation plan_voyage checks berth, which its request does not take",),
            ("client operation plan_voyage checks vessel as Voyage, a name the domain already gives to something else",),
            ("Vessel is checked on a int and on a str: a domain value holds one type",),
        ]
