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
            env={**os.environ, "RESTATE_INGRESS": "http://127.0.0.1:9",
                 "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])},
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
            "[actions.drafter] is named for 'Drafter', which is not a code name in language.toml; a class of actions "
            "is named for the domain term it acts on, never for its port (StoryDrafter)",
        )

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
                '[engine.restate]\ningress_variable = "RESTATE_INGRESS"\n\n[hosts.http]\n'
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
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "LOAN_FILE": str(tmp_path / "loans")}

        render_composition_response = rendering.client.render_composition(render_composition_request)
        tested = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "loans/adapters/repositories", "loans/component"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        typed = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "loans"], cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        store_path = tmp_path / "out" / "loans" / "adapters" / "repositories" / "file_loan_store.py"
        edited = store_path.read_text() + "# the agent's edit\n"
        store_path.write_text(edited)
        second_response = rendering.client.render_composition(render_composition_request)
        check_composition_response = rendering.client.check_composition(
            client.CheckCompositionRequest(composition_dir=str(tmp_path / "composition"), tree_dir=str(tmp_path / "out")),
        )

        assert render_composition_response.problems == ()
        assert tested.returncode == 0, tested.stdout
        assert typed.returncode == 0, typed.stdout
        assert store_path.read_text().startswith("# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here\n")
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
               "MYPYPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")]),
               "LOAN_DB_PATH": str(tmp_path / "loans.sqlite"), "RESTATE_INGRESS": "http://127.0.0.1:9"}

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
        assert 'os.environ.get("LOAN_DB_PATH")' in (tmp_path / "out" / "app" / "app.py").read_text()

    def test_each_routed_story_renders_a_root_test_skeleton_red_at_its_given(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "story-drafting"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert sorted(path for path in render_composition_response.written if path.startswith("tests/")) == [
            "tests/__init__.py", "tests/conftest.py", "tests/test_reading_jtbds_by_jtbd_id.py", "tests/test_submitting_jtbds.py",
        ]
        reading = (tmp_path / "out" / "tests" / "test_reading_jtbds_by_jtbd_id.py").read_text()
        assert reading.startswith("# pragma: tesser-agent-owned;")
        assert "    def test_s_2_a_1(self, host: str) -> None:\n" in reading
        assert "tesser.testing" not in reading
        assert "served" not in reading
        assert "jtbd_id: str | None = None" in reading
        assert (
            "assert jtbd_id is not None, 'write the given of s-2-a-1: I have created a job to be done with POST /jtbds, "
            "and its stories have been drafted'\n"
        ) in reading
        assert reading.index("write the given of") < reading.index('f"{host}/jtbds/{jtbd_id}", data=None,')
        assert "assert status == 200" in reading
        assert "reached_by" not in reading
        assert "time.sleep" not in reading
        assert reading.rstrip().endswith(
            "assert False, 'write the then of s-2-a-1: I get back 200 with status \"awaiting_story_acceptance\" and at least one story, "
            "each with a given, a when, and a then, and in state \"drafted\"' + f\" (answered {answered_body!r})\""
        )
        ast.parse(reading)

    def test_a_tree_with_root_tests_renders_a_generated_conftest_that_takes_the_host_as_pytest_s_host_option(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path / "out"), str(tree.parent / "tesser-py")])}

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        )
        unhosted = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        hosted = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "--host", "http://127.0.0.1:9"],
            cwd=tmp_path / "out", capture_output=True, text=True, check=False, env=env,
        )
        conftest = (tmp_path / "out" / "tests" / "conftest.py").read_text()

        assert render_composition_response.problems == ()
        assert conftest.startswith("# pragma: tesser-generated;")
        assert '    parser.addoption("--host", help="the base URL of the served host, named by the runner")\n' in conftest
        assert '@pytest.fixture(scope="session")\ndef host(request: pytest.FixtureRequest) -> str:\n' in conftest
        assert (tmp_path / "out" / "tests" / "__init__.py").read_text().startswith("# pragma: tesser-generated;")
        assert "pass --host <url>: the runner serves the host and names its address" in unhosted.stdout
        assert "write the given of" in hosted.stdout
        assert "pass --host" not in hosted.stdout

    def test_a_route_with_no_path_value_fails_at_its_given_with_nothing_to_bind(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        )
        submitting = (tmp_path / "out" / "tests" / "test_submitting_loans.py").read_text()

        assert "assert False, 'write the given of s-1-a-1: a borrower and a title'\n" in submitting
        assert "| None" not in submitting
        assert submitting.index("write the given of") < submitting.index("urllib_request.Request(")
        ast.parse(submitting)

    def test_an_edited_root_test_skeleton_is_kept_on_render_again(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))
        render_composition_request = client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "library"), out_dir=str(tmp_path / "out"), printed=())
        rendering.client.render_composition(render_composition_request)
        reading = tmp_path / "out" / "tests" / "test_reading_loans_by_loan_id.py"
        reading.write_text(reading.read_text().replace("loan_id: str | None = None", "loan_id: str | None = 'loan-1'"))
        edited = reading.read_text()

        render_composition_response = rendering.client.render_composition(render_composition_request)

        assert render_composition_response.problems == ()
        assert reading.read_text() == edited
        assert "tests/test_reading_loans_by_loan_id.py" not in render_composition_response.written

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

        assert render_composition_response.problems == ("enum LoanState value lapsed is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

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
            "enum LoanState value lapsed is named by no story: write it in a story's given, when, or then, or remove it from the composition",
            "enum LoanState value open is named by no story: write it in a story's given, when, or then, or remove it from the composition",
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

        assert render_composition_response.problems == ("enum LoanState value loan_i is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

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

        assert render_composition_response.problems == ("enum LoanState value lapsed is named by no story: write it in a story's given, when, or then, or remove it from the composition",)

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
