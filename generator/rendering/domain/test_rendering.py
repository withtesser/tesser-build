from __future__ import annotations

import tesser.testing as ts

import rendering.domain as domain


@ts.helper
def rendered_tree_spec(
    documents: tuple[tuple[str, str, str], ...] = (
        ("language", "read", 'context = "lending"\n'),
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

[[jtbds.stories.jtbds.stories]]
id = "s-1-a-2"
when = "I GET /loans/{loan_id}"
then = "I get back 200 with its borrower"
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
app = "library"

[implementations.LoanRepository.memory]
body = "supported"

[implementations.LoanIdentityRepository.uuid]
body = "supported"

[engine.restate]
body = "supported"
ingress_variable = "RESTATE_INGRESS"
admin_variable = "RESTATE_ADMIN"
callback_host_variable = "RESTATE_CALLBACK_HOST"

[environments.gate]
implementations = { LoanRepository = "memory", LoanIdentityRepository = "uuid" }
engine = "restate"
hosts = ["http"]

[hosts.http]
engine_path = "/restate"
listen_port_variable = "LIBRARY_PORT"
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
) -> domain.RenderedTreeSpec:
    return domain.RenderedTreeSpec(documents=documents, pieces=pieces, target=target, existing=existing)


class TestRenderedTree:

    def test_a_piece_renders_once_for_each_item_its_path_enters(self) -> None:
        rendered_tree = domain.RenderedTree(rendered_tree_spec())

        assert rendered_tree.health() == domain.Health.CLEAN
        assert {str(rendered_file.path()): str(rendered_file.content()) for rendered_file in rendered_tree.files()} == {
            "lending/ports/loan_repository.txt": "# pragma: tesser-generated; x\nLoanRepository stores LoanStore\n",
            "lending/ports/loan_identity_repository.txt": "# pragma: tesser-generated; x\nLoanIdentityRepository\n",
            "lending/domain/loan.txt": "# pragma: tesser-agent-owned; x\nLoan by loan_id\n",
            "routes.txt": "POST /loans 201\nGET /loans/{loan_id} 200\n",
        }

    def test_an_agent_owned_file_already_in_the_output_is_kept_as_it_is(self) -> None:
        rendered_tree = domain.RenderedTree(
            rendered_tree_spec(target="occupied", existing=(("lending/domain/loan.txt", "the agent's own loan\n"),))
        )

        assert [str(text) for text in rendered_tree.kept()] == ["lending/domain/loan.txt"]
        assert "lending/domain/loan.txt" not in [str(rendered_file.path()) for rendered_file in rendered_tree.files()]

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
