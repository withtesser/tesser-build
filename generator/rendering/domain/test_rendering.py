from __future__ import annotations

import tesser.testing as ts

import rendering.domain as domain


@ts.helper
def rendered_tree_spec(
    documents: tuple[tuple[str, str, str], ...] = (
        ("language", "read", 'context = "lending"\n\n[[terms]]\nterm = "loan"\nmeans = "A book lent to a borrower."\ncode_names = ["Loan"]\n'),
        (
            "story",
            "read",
            """
[[jtbds]]
id = "j-root"
level = 1

[[jtbds.stories]]
id = "s-1"

[[jtbds.stories.jtbds]]
id = "j-1-a"
level = 2

[[jtbds.stories.jtbds.stories]]
id = "s-1-a-1"
when = "I POST a borrower as JSON to /loans"
then = "I get back 201 with its loan_id"
route = "POST /loans"
status = 201

[[jtbds.stories.jtbds.stories]]
id = "s-1-a-2"
when = "I GET /loans/{loan_id}"
then = "I get back 200 with its borrower"
route = "GET /loans/{loan_id}"
status = 200
""",
        ),
        (
            "infra",
            "read",
            """
app = "library"

[runtime]
language = "python"
version = "3.12"

[engine.restate]
body = "supported"
engine_path = "/restate"
engine_url_variable = "RESTATE_URL"

[hosts.http]
listen_port_variable = "LIBRARY_PORT"

[storage.memory]
""",
        ),
        (
            "composition",
            "read",
            """
context = "lending"

[aggregate]
name = "Loan"
identity = "loan_id"

[aggregate.spec]
loan_id = "str"
borrower = "str"

[aggregate.reads]
loan_id = "str"
borrower = "str"

[interfaces.http]
serves = ["s-1-a-1", "s-1-a-2"]

[client.operations.lend_book]
request = ["borrower"]
response = ["loan_id"]
steps = ["identity.issue_loan_id", "orchestrator.run_arrange_loan"]
serves = ["s-1-a-1"]

[client.operations.get_loan]
request = ["loan_id"]
response = ["loan_id", "borrower"]
steps = ["repository.load_loan"]
serves = ["s-1-a-2"]

[orchestrator.operations.arrange_loan]
request = ["loan_id", "borrower"]
response = ["loan_id"]
steps = ["actions.loan.record_loan"]

[actions.loan]
port = "LoanRepository"

[actions.loan.operations.record_loan]
builds = "Loan"
calls = "save_loan"
request = ["loan_id", "borrower"]
response = ["loan_id"]

[ports.LoanRepository]
operations.save_loan = { request = ["loan"], response = [] }
operations.load_loan = { request = ["loan_id"], response = ["loan"] }

[ports.LoanIdentityRepository]
operations.issue_loan_id = { request = [], response = ["loan_id"] }
""",
        ),
        (
            "implementations",
            "read",
            """
[implementations.LoanRepository.memory]
body = "supported"

[implementations.LoanIdentityRepository.uuid]
body = "supported"

[environments.gate]
implementations = { LoanRepository = "memory", LoanIdentityRepository = "uuid" }
engine = "restate"
hosts = ["http"]
""",
        ),
        ("generator", "read", '[sample_values]\nloan_id = ["loan-1", "loan-2"]\nborrower = ["Ada", "Grace"]\n'),
    ),
    pieces: tuple[tuple[str, str], ...] = (
        ("{{context}}/ports/{{#ports}}/{{module}}.txt.tmpl", "# pragma: tesser-generated; x\n{{Port}}{{#store}} stores {{Store}}{{/store}}\n"),
        ("{{context}}/domain/{{aggregate}}.txt.tmpl", "# pragma: tesser-agent-owned; x\n{{Aggregate}} by {{identity}}\n"),
        ("routes.txt.tmpl", "{{#routes}}\n{{method}} {{path}} {{status}}\n{{/routes}}"),
    ),
    target: str = "absent",
    existing: tuple[tuple[str, str], ...] = (),
    printed: tuple[str, ...] = (),
    composition: str = "compositions/lending",
) -> domain.RenderedTreeSpec:
    return domain.RenderedTreeSpec(
        documents=documents, pieces=pieces, target=target, existing=existing, printed=printed, composition=composition
    )


class TestRenderedTree:

    def test_a_printed_path_answers_what_the_render_leaves_there(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            existing=(("lending/domain/loan.txt", "an edited loan\n"),),
            printed=("routes.txt", "lending/domain/loan.txt"),
        ))

        assert [(str(printed.path()), str(printed.content())) for printed in rendered_tree.printed()] == [
            ("routes.txt", "POST /loans 201\nGET /loans/{loan_id} 200\n"),
            ("lending/domain/loan.txt", "an edited loan\n"),
        ]

    def test_a_printed_path_the_composition_does_not_render_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(printed=("tests/test_nope.py",)))

        assert ([str(problem) for problem in rendered_tree.problems()], rendered_tree.printed()) == (
            ["--print names tests/test_nope.py, which the composition does not render"], (),
        )

    def test_a_printed_pattern_answers_every_rendered_path_it_matches_in_order(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(printed=("lending/*/*.txt",)))

        assert [str(printed.path()) for printed in rendered_tree.printed()] == [
            "lending/domain/loan.txt", "lending/ports/loan_identity_repository.txt", "lending/ports/loan_repository.txt",
        ]

    def test_a_printed_pattern_that_matches_nothing_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(printed=("tests/test_*.py",)))

        assert ([str(problem) for problem in rendered_tree.problems()], rendered_tree.printed()) == (
            ["--print names tests/test_*.py, which matches nothing the composition renders"], (),
        )

    def test_a_piece_renders_once_for_each_item_its_path_enters(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec())

        assert rendered_tree.health() == domain.Health.CLEAN
        assert {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in rendered_tree.files()} == {
            "lending/ports/loan_repository.txt": "# pragma: tesser-generated; x\nLoanRepository stores LoanStore\n",
            "lending/ports/loan_identity_repository.txt": "# pragma: tesser-generated; x\nLoanIdentityRepository\n",
            "lending/domain/loan.txt": "# pragma: tesser-agent-owned; x\nLoan by loan_id\n",
            "routes.txt": "POST /loans 201\nGET /loans/{loan_id} 200\n",
            ".tesser-rendered": "compositions/lending\n"
            "88e210352514d935\tlending/domain/loan.txt\t*\n"
            "0777370abdd2d0c8\tlending/ports/loan_identity_repository.txt\t*\n"
            "f4438a30af16da24\tlending/ports/loan_repository.txt\t*\n"
            "721d3a67fdb038b1\troutes.txt\t*\n",
        }

    def test_a_render_names_its_composition_in_tesser_rendered_so_the_tree_is_checked_against_it(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(composition="generator/compositions/lending"))

        assert [str(rendered_file.content()).split("\n", 1)[0] for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == ".tesser-rendered"] == ["generator/compositions/lending"]

    def test_an_agent_owned_file_already_in_the_output_is_kept_as_it_is(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(target="occupied", existing=(("lending/domain/loan.txt", "the agent's own loan\n"),))
        )

        assert [str(text) for text in rendered_tree.kept()] == ["lending/domain/loan.txt"]
        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/domain/loan.txt"] == ["the agent's own loan\n"]

    def test_a_file_the_renderer_does_not_write_is_left_beside_the_tree(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(target="occupied", existing=(("README.md", "# lending\n"),)))

        assert rendered_tree.health() == domain.Health.CLEAN
        assert "README.md" not in [str(rendered_file.path()) for rendered_file in rendered_tree.files()]

    def test_a_file_it_would_write_the_same_is_written_again(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(target="occupied", existing=(("lending/ports/loan_repository.txt", "# pragma: tesser-generated; x\nLoanRepository stores LoanStore\n"),))
        )

        assert rendered_tree.health() == domain.Health.CLEAN
        assert "lending/ports/loan_repository.txt" in [str(rendered_file.path()) for rendered_file in rendered_tree.files()]

    def test_a_generated_file_already_in_the_output_is_overwritten(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(target="occupied", existing=(("lending/ports/loan_repository.txt", "# pragma: tesser-generated; x\nOld\n"),))
        )

        assert rendered_tree.health() == domain.Health.CLEAN
        assert "lending/ports/loan_repository.txt" in [str(rendered_file.path()) for rendered_file in rendered_tree.files()]

    def test_an_unmarked_file_where_a_generated_one_goes_is_a_problem_and_nothing_is_written(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(target="occupied", existing=(("lending/ports/loan_repository.txt", "hand written\n"),))
        )

        assert [str(text) for text in rendered_tree.problems()] == [
            "the output directory already has lending/ports/loan_repository.txt, which is not marked generated, "
            "so the renderer will not replace it"
        ]
        assert rendered_tree.files() == ()

    def test_drift_names_each_generated_file_that_differs_is_missing_or_lost_its_mark(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(
                target="occupied",
                existing=(
                    ("lending/ports/loan_repository.txt", "# pragma: tesser-generated; x\nEdited\n"),
                    ("lending/ports/loan_identity_repository.txt", "LoanIdentityRepository\n"),
                    ("lending/domain/loan.txt", "the agent's own loan\n"),
                    ("routes.txt", "POST /loans 201\nGET /loans/{loan_id} 200\n"),
                    (".tesser-rendered", "compositions/lending\n"),
                ),
            )
        )

        assert [str(text) for text in rendered_tree.drift()] == [
            "lending/ports/loan_identity_repository.txt has lost its generated mark",
            "lending/ports/loan_repository.txt differs from what the composition renders",
        ]

    def test_a_missing_generated_file_is_drift(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(target="absent"))

        assert "routes.txt is missing" in [str(text) for text in rendered_tree.drift()]

    def test_two_pieces_that_render_one_path_are_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(pieces=(("x.txt.tmpl", "a"), ("{{#ports}}/x.txt.tmpl", "b"))))

        assert [str(text) for text in rendered_tree.problems()] == ["two pieces render x.txt, and a render writes each path once"]

    def test_a_piece_whose_path_leaves_the_output_directory_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(pieces=(("{{context}}/../../x.txt.tmpl", "a"),)))

        assert [str(text) for text in rendered_tree.problems()] == [
            "a piece renders the path 'lending/../../x.txt', which leaves the output directory"
        ]

    def test_a_missing_document_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(documents=(("language", "missing", ""),)))

        assert [str(text) for text in rendered_tree.problems()] == [
            "the composition's language.toml is missing",
            "the composition has no story.toml",
            "the composition has no infra.toml, which says what the app runs on and what an operator must provide",
            "the composition has no composition.toml",
            "the composition has no implementations.toml",
            "the composition has no generator.toml",
        ]

    def test_a_piece_that_names_what_nothing_binds_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(pieces=(("x.txt.tmpl", "{{nothing_here}}"),)))

        assert [str(text) for text in rendered_tree.problems()] == ["a template names {{nothing_here}}, which nothing binds"]

    def test_an_output_path_that_is_a_file_is_a_problem(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec(target="not_directory"))

        assert [str(text) for text in rendered_tree.problems()] == ["the output directory is a file"]

    def test_a_render_keeps_each_definition_written_by_hand_and_renders_the_rest(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", (
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n{{#routes}}\n\n"
            "    def {{operation}}(self) -> str:\n        return \"{{method}} {{path}}\"\n{{/routes}}\n"
        )),)
        first = domain.RenderedTree(rendered_tree_spec(pieces=pieces))
        written = {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in first.files()}
        handler = written["lending/handlers.py"].replace('return "GET /loans/{loan_id}"', 'return "read by hand"') + (
            "\n\nclass Extra:\n\n    def help(self) -> str:\n        return \"added by hand\"\n"
        )

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=pieces, target="occupied", existing=tuple({**written, "lending/handlers.py": handler}.items()),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/handlers.py"] == [handler]
        assert ([str(text) for text in rendered_tree.kept()], rendered_tree.drift()) == (["lending/handlers.py"], ())

    def test_a_definition_the_composition_renders_differently_follows_it_and_one_edited_by_hand_stays_and_is_named(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", (
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n{{#routes}}\n\n"
            "    def {{operation}}(self) -> str:\n        return \"{{method}} {{path}}\"\n{{/routes}}\n"
        )),)
        first = domain.RenderedTree(rendered_tree_spec(pieces=pieces))
        written = {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in first.files()}
        handler = written["lending/handlers.py"].replace('return "GET /loans/{loan_id}"', 'return "read by hand"')

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=((pieces[0][0], pieces[0][1].replace("{{path}}", "{{path}} again")),),
            target="occupied", existing=tuple({**written, "lending/handlers.py": handler}.items()),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/handlers.py"] == [
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n\n"
            "    def lend_book(self) -> str:\n        return \"POST /loans again\"\n\n"
            "    def get_loan(self) -> str:\n        return \"read by hand\"\n"
        ]
        assert [str(text) for text in rendered_tree.kept()] == [
            "lending/handlers.py",
            "lending/handlers.py: Handler.get_loan, written by hand, which the composition now renders differently",
        ]
        assert [str(text) for text in rendered_tree.drift()] == [
            "lending/handlers.py: Handler.lend_book differs from what the composition renders",
            "lending/handlers.py: Handler.get_loan was edited by hand, and the composition now renders it differently",
        ]

    def test_a_definition_missing_from_a_file_is_rendered_back_after_the_one_before_it(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", (
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n{{#routes}}\n\n"
            "    def {{operation}}(self) -> str:\n        return \"{{method}} {{path}}\"\n{{/routes}}\n"
        )),)
        first = domain.RenderedTree(rendered_tree_spec(pieces=pieces))
        written = {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in first.files()}
        handler = written["lending/handlers.py"].replace(
            '\n    def get_loan(self) -> str:\n        return "GET /loans/{loan_id}"\n',
            '\n    def help(self) -> str:\n        return "added by hand"\n',
        )

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=pieces, target="occupied", existing=tuple({**written, "lending/handlers.py": handler}.items()),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/handlers.py"] == [
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n\n"
            "    def lend_book(self) -> str:\n        return \"POST /loans\"\n\n"
            "    def get_loan(self) -> str:\n        return \"GET /loans/{loan_id}\"\n\n"
            "    def help(self) -> str:\n        return \"added by hand\"\n"
        ]
        assert [str(text) for text in rendered_tree.drift()] == ["lending/handlers.py: Handler.get_loan is missing"]

    def test_a_definition_no_longer_rendered_goes_unless_it_was_edited_by_hand(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", (
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n{{#routes}}\n\n"
            "    def {{operation}}(self) -> str:\n        return \"{{method}} {{path}}\"\n{{/routes}}\n"
        )),)
        first = domain.RenderedTree(rendered_tree_spec(pieces=pieces))
        written = {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in first.files()}
        handler = written["lending/handlers.py"].replace('return "GET /loans/{loan_id}"', 'return "read by hand"')

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=((pieces[0][0], pieces[0][1].replace("def {{operation}}(", "def {{operation}}_now(")),),
            target="occupied", existing=tuple({**written, "lending/handlers.py": handler}.items()),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/handlers.py"] == [
            "# pragma: tesser-generated; x\nfrom __future__ import annotations\n\n\nclass Handler:\n\n"
            "    def lend_book_now(self) -> str:\n        return \"POST /loans\"\n\n"
            "    def get_loan_now(self) -> str:\n        return \"GET /loans/{loan_id}\"\n\n"
            "    def get_loan(self) -> str:\n        return \"read by hand\"\n"
        ]
        assert [str(text) for text in rendered_tree.drift()] == [
            "lending/handlers.py: Handler.lend_book is no longer rendered",
            "lending/handlers.py: Handler.lend_book_now is missing",
            "lending/handlers.py: Handler.get_loan_now is missing",
        ]

    def test_a_file_that_does_not_parse_is_a_problem_and_nothing_is_written(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", "# pragma: tesser-generated; x\nclass Handler:\n    pass\n"),)
        first = domain.RenderedTree(rendered_tree_spec(pieces=pieces))
        written = {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in first.files()}

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=pieces, target="occupied", existing=tuple({**written, "lending/handlers.py": "class Handler(:\n"}.items()),
        ))

        assert [str(text) for text in rendered_tree.problems()] == [
            "lending/handlers.py does not parse (line 1: invalid syntax), so the render cannot keep what is written in it by hand"
        ]
        assert rendered_tree.files() == ()

    def test_a_generated_file_from_a_render_that_kept_no_records_is_rendered_over(self) -> None:
        pieces = (("{{context}}/handlers.py.tmpl", "# pragma: tesser-generated; x\nclass Handler:\n    pass\n"),)

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=pieces, target="occupied", existing=(
                ("lending/handlers.py", "# pragma: tesser-generated; x\nclass Handler:\n    pass\n\n\nclass Old:\n    pass\n"),
                (".tesser-rendered", "compositions/lending\n"),
            ),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/handlers.py"] == ["# pragma: tesser-generated; x\nclass Handler:\n    pass\n"]

    def test_an_agent_owned_file_from_a_render_that_kept_no_records_keeps_its_definitions_and_gains_the_missing_ones(self) -> None:
        pieces = (("{{context}}/loan.py.tmpl", (
            "# pragma: tesser-agent-owned; x\nimport enum\n\n\nclass Loan:\n\n    def lend(self) -> str:\n        return \"\"\n\n"
            "    def extend(self) -> str:\n        return \"\"\n"
        )),)

        rendered_tree = domain.RenderedTree(rendered_tree_spec(
            pieces=pieces, target="occupied", existing=(
                ("lending/loan.py", "import enum\nimport json\n\n\nclass Loan:\n\n    def lend(self) -> str:\n        return json.dumps(\"lent\")\n"),
            ),
        ))

        assert [str(rendered_file.content()) for rendered_file in rendered_tree.files()
                if str(rendered_file.path()) == "lending/loan.py"] == [
            "# pragma: tesser-agent-owned; x\nimport enum\nimport json\n\n\nclass Loan:\n\n"
            "    def lend(self) -> str:\n        return json.dumps(\"lent\")\n\n    def extend(self) -> str:\n        return \"\"\n"
        ]
