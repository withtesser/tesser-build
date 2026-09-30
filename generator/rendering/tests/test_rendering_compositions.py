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
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}/title\"\nthen = \"I get back 200 with its title\"\nroute = \"GET /loans/{loan_id}/title\"\nstatus = 200\nreached_by = [{ route = \"POST /loans\" }]\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.get_title]\nrequest = [\"loan_id\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I PUT a title as JSON to /loans/{loan_id}\"\nthen = \"I get back 200 with its title\"\nroute = \"PUT /loans/{loan_id}\"\nstatus = 200\nreached_by = [{ route = \"POST /loans\" }]\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.retitle_loan]\nrequest = [\"loan_id\", \"title\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\", \"repository.save_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "generator.toml": [('title = ["Middlemarch", "Beloved"]', 'title = ["Middlemarch", "Beloved"]\ncopies = [1, 2]')],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
                "[hosts.http]",
                "[environments.local]\nimplementations = { LoanRepository = \"memory\", LoanIdentityRepository = \"uuid\" }\n"
                "engine = \"restate\"\nhosts = [\"http\"]\n\n[hosts.http]",
            )],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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

    def test_each_routed_story_renders_a_root_test_skeleton_red_at_its_then(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tree / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tree / "compositions" / "story-drafting"), out_dir=str(tmp_path / "out"), printed=())
        )

        assert render_composition_response.problems == ()
        assert sorted(path for path in render_composition_response.written if path.startswith("tests/")) == [
            "tests/__init__.py", "tests/test_reading_jtbds.py", "tests/test_submitting_jtbds.py",
        ]
        reading = (tmp_path / "out" / "tests" / "test_reading_jtbds.py").read_text()
        assert reading.startswith("# pragma: tesser-agent-owned;")
        assert 'host = ts.served("STORY_DRAFTING_HOST")' in reading
        assert 'given_jtbd_id = answered["jtbd_id"]' in reading
        assert "for _ in range(40):" in reading
        assert "if answered.get(\"status\") == 'awaiting_story_acceptance':" in reading
        assert 'f"{host}/jtbds/{given_jtbd_id}", data=None,' in reading
        assert "assert status == 200" in reading
        assert reading.rstrip().endswith(
            "assert False, 'write the then of s-2-a-1: I get back 200 with status \"awaiting_story_acceptance\" and at least one story, "
            "each with a given, a when, and a then, and in state \"drafted\"' + f\" (answered {answered_body!r})\""
        )
        ast.parse(reading)

    def test_a_reached_by_step_that_names_no_story_route_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('reached_by = [{ route = "POST /loans" }]', 'reached_by = [{ route = "POST /books" }]')],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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

        assert render_composition_response.problems == ("s-1-b-1's reached_by names 'POST /books', which is no level-2 story's route",)

    def test_a_route_field_its_reached_by_never_answers_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('reached_by = [{ route = "POST /loans" }]\n', "")],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "s-1-b-1 reaches GET /loans/{loan_id}, and nothing before it in its reached_by answers loan_id",
        )

    def test_polling_until_a_field_the_step_does_not_answer_is_a_problem(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        edits = {
            "story.toml": [('until = { status = "awaiting_story_acceptance" }', 'until = { stage = "awaiting_story_acceptance" }')],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "s-2-a-1's reached_by polls GET /jtbds/{jtbd_id} until stage, which it does not answer",
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}\"\nthen = \"I get back 200 with its title\"\nroute = \"GET /loans/{loan_id}\"\nstatus = 200\nreached_by = [{ route = \"POST /loans\" }]\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
            "composition.toml": [
                ('serves = ["s-1-a-1", "s-1-b-1"]', 'serves = ["s-1-a-1", "s-1-b-1", "s-1-c-1"]'),
                ("[orchestrator.operations.arrange_loan]", "[client.operations.get_title]\nrequest = [\"loan_id\"]\nresponse = [\"title\"]\nsteps = [\"repository.load_loan\"]\nserves = [\"s-1-c-1\"]\n\n[orchestrator.operations.arrange_loan]"),
            ],
        }
        for name in ("language", "story", "composition", "implementations", "generator"):
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
            "story.toml": [("[[jtbds.stories.jtbds]]\nid = \"j-1-b\"", "[[jtbds.stories.jtbds]]\nid = \"j-1-c\"\nlevel = 2\n\n[[jtbds.stories.jtbds.stories]]\nid = \"s-1-c-1\"\nwhen = \"I GET /loans/{loan_id}/copies/{copies}\"\nthen = \"I get back 200 with its loan_id\"\nroute = \"GET /loans/{loan_id}/copies/{copies}\"\nstatus = 200\nreached_by = [{ route = \"POST /loans\" }, { route = \"GET /loans/{loan_id}\" }]\n\n[[jtbds.stories.jtbds]]\nid = \"j-1-b\"")],
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
        for name in ("language", "story", "composition", "implementations", "generator"):
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
