from __future__ import annotations

import pytest

import tesser.testing as ts

import trees.domain as domain


@ts.helper
def tree_spec(
    state: str = "read",
    note: str = "spec.toml",
    unknown_keys: tuple[str, ...] = (),
    target: str = "absent",
    existing: tuple[tuple[str, str], ...] = (),
    app_name: str = "voice",
    bounded_context_name: str = "calls",
    aggregate_root_class_name: str = "Call",
    durable_execution_engine: str = "restate",
    storage: str = "postgres",
    host: str = "cli",
    identity_field_name: str = "call_id",
    identity_port_operation_name: str = "issue_call_id",
    aggregate_fields: tuple[tuple[str, str], ...] = (("person_name", "str"), ("phone_number", "str")),
    sample_values: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
        ("call_id", (("str", "call-1"), ("str", "call-2"))),
        ("person_name", (("str", "Ada"), ("str", "Grace"))),
        ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
    ),
    write_operation_name: str = "place_call",
    read_operation_name: str = "get_call",
    read_response_fields: tuple[str, ...] = ("call_id", "person_name"),
    orchestrator_operation_name: str = "conduct_call",
    action_operation_name: str = "record_call",
    save_operation_name: str = "save_call",
    load_operation_name: str = "load_call",
    load_response_collection_name: str = "calls",
    test_class_name: str = "TestPlacingCalls",
    test_method_name: str = "test_a_call_is_successfully_made",
    asserted_field: str = "person_name",
    random_values: tuple[tuple[str, str], ...] = (("str", "Ada"),),
    storage_url_variable: str = "CALLS_STORAGE",
    restate_ingress_url_variable: str = "RESTATE_INGRESS",
    host_url_variable: str = "",
    templates: tuple[tuple[str, str], ...] = (("{{context}}/domain/{{aggregate}}.py.tmpl", "class {{Aggregate}}:\n"),),
) -> domain.TreeSpec:
    return domain.TreeSpec(
        state=state,
        note=note,
        unknown_keys=unknown_keys,
        target=target,
        existing=existing,
        app_name=app_name,
        bounded_context_name=bounded_context_name,
        aggregate_root_class_name=aggregate_root_class_name,
        durable_execution_engine=durable_execution_engine,
        storage=storage,
        host=host,
        identity_field_name=identity_field_name,
        identity_port_operation_name=identity_port_operation_name,
        aggregate_fields=aggregate_fields,
        sample_values=sample_values,
        write_operation_name=write_operation_name,
        read_operation_name=read_operation_name,
        read_response_fields=read_response_fields,
        orchestrator_operation_name=orchestrator_operation_name,
        action_operation_name=action_operation_name,
        save_operation_name=save_operation_name,
        load_operation_name=load_operation_name,
        load_response_collection_name=load_response_collection_name,
        test_class_name=test_class_name,
        test_method_name=test_method_name,
        asserted_field=asserted_field,
        random_values=random_values,
        storage_url_variable=storage_url_variable,
        restate_ingress_url_variable=restate_ingress_url_variable,
        host_url_variable=host_url_variable,
        templates=templates,
    )


class TestTreeRendering:

    def test_a_template_path_and_its_text_render_from_the_spec(self) -> None:
        tree = domain.Tree(
            tree_spec(
                bounded_context_name="calls",
                aggregate_root_class_name="Call",
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "class {{Aggregate}}:\n"),),
            )
        )

        assert tree.health() is domain.Health.CLEAN
        assert [(str(generated_file.path()), str(generated_file.content())) for generated_file in tree.files()] == [
            ("calls/domain/call.py", "class Call:\n")
        ]

    def test_a_pascal_case_aggregate_root_names_its_modules_in_snake_case(self) -> None:
        tree = domain.Tree(
            tree_spec(
                bounded_context_name="calls",
                aggregate_root_class_name="PurchaseOrder",
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{aggregate}} {{Aggregate}}"),),
            )
        )

        assert [(str(generated_file.path()), str(generated_file.content())) for generated_file in tree.files()] == [
            ("calls/domain/purchase_order.py", "purchase_order PurchaseOrder")
        ]

    def test_a_list_section_repeats_once_per_field_and_the_last_takes_no_comma(self) -> None:
        tree = domain.Tree(
            tree_spec(
                identity_field_name="call_id",
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "({{#record_fields}}{{field}}: {{py_type}}{{comma}}{{/record_fields}})"),),
            )
        )

        assert str(tree.files()[0].content()) == "(call_id: str, person_name: str, phone_number: str)"

    def test_a_section_alone_on_its_line_takes_its_line_with_it(self) -> None:
        tree = domain.Tree(
            tree_spec(
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "a\n{{#fields}}\n{{field}}\n{{/fields}}\nb\n"),),
            )
        )

        assert str(tree.files()[0].content()) == "a\nperson_name\nphone_number\nb\n"

    def test_a_field_flag_opens_and_inverts_a_section_inside_a_list_section(self) -> None:
        tree = domain.Tree(
            tree_spec(
                identity_field_name="call_id",
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{#record_fields}}{{#is_identity}}{{Field}}:{{/is_identity}}"
                        "{{^is_identity}}{{field}} {{/is_identity}}{{/record_fields}}",
                    ),
                ),
            )
        )

        assert str(tree.files()[0].content()) == "CallId:person_name phone_number "

    def test_the_prose_joins_three_fields_with_commas_and_a_final_and(self) -> None:
        tree = domain.Tree(
            tree_spec(
                identity_field_name="call_id",
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{#record_fields}}{{prose}}a {{field}}{{/record_fields}}"),),
            )
        )

        assert str(tree.files()[0].content()) == "a call_id, a person_name, and a phone_number"

    def test_the_sample_values_render_as_literals_beside_a_value_of_the_wrong_type(self) -> None:
        tree = domain.Tree(
            tree_spec(
                identity_field_name="call_id",
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("str", "Ada"), ("str", "Grace"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{#record_fields}}{{field}}={{sample}}/{{sample2}}/{{wrong}};{{/record_fields}}"),),
            )
        )

        assert str(tree.files()[0].content()) == (
            'call_id="call-1"/"call-2"/1;person_name="Ada"/"Grace"/1;phone_number="+15555550100"/"+15555550101"/1;'
        )

    def test_an_int_field_renders_unquoted_samples_and_its_int_exit(self) -> None:
        tree = domain.Tree(
            tree_spec(
                aggregate_fields=(("person_name", "int"), ("phone_number", "str")),
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("int", "1"), ("int", "2"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
                random_values=(("int", "3"),),
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{#fields}}{{field}}={{sample}} {{wrong}} {{dunder}} {{sql_type}};{{/fields}}{{random_choices}}",
                    ),
                ),
            )
        )

        assert str(tree.files()[0].content()) == (
            'person_name=1 "1" __int__ bigint;phone_number="+15555550100" 1 __str__ text;(3,)'
        )

    def test_a_field_carries_its_argument_index_its_cli_reader_and_whether_the_acceptance_test_asserts_it(
        self,
    ) -> None:
        tree = domain.Tree(
            tree_spec(
                aggregate_fields=(("person_name", "int"), ("phone_number", "str")),
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("int", "1"), ("int", "2"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
                random_values=(("int", "3"),),
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{field_count}}:{{#fields}}{{index}} {{cli_arg}} {{sample_arg}}"
                        "{{#is_asserted}} asserted{{/is_asserted}};{{/fields}}",
                    ),
                ),
            )
        )

        assert str(tree.files()[0].content()) == '2:0 int_arg "1" asserted;1 arg "+15555550100";'

    def test_the_names_the_spec_gives_and_the_names_derived_from_them(self) -> None:
        tree = domain.Tree(
            tree_spec(
                app_name="voice",
                identity_field_name="call_id",
                identity_port_operation_name="issue_call_id",
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("str", "Ada"), ("str", "Grace"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
                orchestrator_operation_name="conduct_call",
                load_response_collection_name="calls",
                test_class_name="TestPlacingCalls",
                test_method_name="test_a_call_is_successfully_made",
                random_values=(("str", "Ada"),),
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{Identity}} {{issue}} {{Issue}} {{Conduct}} {{conduct_words}} {{App}}App "
                        "{{collection}} {{identity_raw}} {{test_class}}.{{test_method}} {{random_choices}}",
                    ),
                ),
            )
        )

        assert str(tree.files()[0].content()) == (
            "CallId issue_call_id IssueCallId ConductCall conduct call VoiceApp "
            'calls call-1 TestPlacingCalls.test_a_call_is_successfully_made ("Ada",)'
        )

    def test_a_name_the_spec_does_not_bind_is_a_template_error(self) -> None:
        with pytest.raises(ValueError):
            domain.Tree(tree_spec(templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{nothing}}"),)))

    def test_a_section_that_never_closes_is_a_template_error(self) -> None:
        with pytest.raises(ValueError):
            domain.Tree(tree_spec(templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{#fields}}never closed"),)))


    def test_a_field_carries_its_http_body_reader(self) -> None:
        tree = domain.Tree(
            tree_spec(
                aggregate_fields=(("person_name", "int"), ("phone_number", "str")),
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("int", "1"), ("int", "2"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
                random_values=(("int", "3"),),
                templates=(("{{context}}/domain/{{aggregate}}.py.tmpl", "{{#fields}}{{field}} {{http_arg}};{{/fields}}"),),
            )
        )

        assert str(tree.files()[0].content()) == "person_name integer;phone_number text;"

    def test_a_guard_directory_keeps_its_files_only_when_its_section_opens_and_leaves_the_path(self) -> None:
        tree = domain.Tree(
            tree_spec(
                storage="postgres",
                host="cli",
                templates=(
                    ("{{#storage_postgres}}/pgdatabase/database.py.tmpl", "postgres"),
                    ("{{#storage_memory}}/memory.py.tmpl", "memory"),
                    ("srv/{{#host_cli}}/cli/main.py.tmpl", "cli"),
                    ("srv/{{^host_cli}}/http/main.py.tmpl", "http"),
                ),
            )
        )

        assert [(str(generated_file.path()), str(generated_file.content())) for generated_file in tree.files()] == [
            ("pgdatabase/database.py", "postgres"),
            ("srv/cli/main.py", "cli"),
        ]

    def test_an_absent_storage_and_host_are_postgres_and_cli(self) -> None:
        tree = domain.Tree(
            tree_spec(
                storage="",
                host="",
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{storage}}{{#storage_postgres}} postgres{{/storage_postgres}}{{#storage_memory}} memory{{/storage_memory}}"
                        "{{#host_cli}} cli{{/host_cli}}{{#host_http}} http{{/host_http}}",
                    ),
                ),
            )
        )

        assert str(tree.files()[0].content()) == "postgres postgres cli"

    def test_a_memory_store_behind_an_http_host_names_the_host_variable_and_no_storage_variable(self) -> None:
        tree = domain.Tree(
            tree_spec(
                storage="memory",
                host="http",
                storage_url_variable="",
                host_url_variable="VOICE_HOST",
                templates=(
                    (
                        "{{context}}/domain/{{aggregate}}.py.tmpl",
                        "{{storage}} {{host_env}}{{#storage_memory}} memory{{/storage_memory}}{{#host_http}} http{{/host_http}}",
                    ),
                ),
            )
        )

        assert tree.health() is domain.Health.CLEAN
        assert str(tree.files()[0].content()) == "memory VOICE_HOST memory http"


class TestTreeProblems:

    def test_an_engine_without_templates_is_a_problem_and_nothing_renders(self) -> None:
        tree = domain.Tree(tree_spec(durable_execution_engine="temporal"))

        assert tree.health() is domain.Health.PROBLEMS
        assert [str(text) for text in tree.problems()] == [
            "durable_execution_engine 'temporal' has no templates; the one engine is 'restate'"
        ]
        assert tree.files() == ()

    def test_a_storage_without_templates_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(storage="sqlite", storage_url_variable=""))

        assert [str(text) for text in tree.problems()] == [
            "storage 'sqlite' has no templates; a storage is one of postgres, memory"
        ]

    def test_a_host_without_templates_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(host="grpc"))

        assert [str(text) for text in tree.problems()] == ["host 'grpc' has no templates; a host is one of cli, http"]

    def test_a_memory_store_behind_a_cli_host_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(storage="memory", host="cli", storage_url_variable=""))

        assert [str(text) for text in tree.problems()] == [
            "storage 'memory' needs host 'http': a cli host reads in a process of its own, "
            "so it never sees the store the served Restate endpoint writes"
        ]

    def test_a_postgres_store_without_its_storage_variable_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(storage="postgres", storage_url_variable=""))

        assert [str(text) for text in tree.problems()] == [
            "the spec names no environment_variables.storage_url, which a postgres store reads"
        ]

    def test_a_memory_store_with_a_storage_variable_is_a_problem(self) -> None:
        tree = domain.Tree(
            tree_spec(storage="memory", host="http", storage_url_variable="CALLS_STORAGE", host_url_variable="VOICE_HOST")
        )

        assert [str(text) for text in tree.problems()] == [
            "the spec names environment_variables.storage_url, which only a postgres store reads"
        ]

    def test_an_http_host_without_its_host_variable_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(host="http", host_url_variable=""))

        assert [str(text) for text in tree.problems()] == [
            "the spec names no environment_variables.host_url, which an http host reads"
        ]

    def test_a_cli_host_with_a_host_variable_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(host="cli", host_url_variable="VOICE_HOST"))

        assert [str(text) for text in tree.problems()] == [
            "the spec names environment_variables.host_url, which only an http host reads"
        ]

    def test_a_host_variable_that_is_not_upper_case_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(host="http", host_url_variable="voice_host"))

        assert [str(text) for text in tree.problems()] == [
            "environment_variables.host_url 'voice_host' is not an upper-case environment variable name"
        ]

    def test_a_key_the_spec_does_not_take_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(unknown_keys=("client.write_operation",)))

        assert [str(text) for text in tree.problems()] == [
            "the spec names 'client.write_operation', which is not a key the spec takes"
        ]

    def test_a_missing_spec_file_is_the_one_problem(self) -> None:
        tree = domain.Tree(tree_spec(state="missing", note="spec.toml"))

        assert [str(text) for text in tree.problems()] == ["there is no spec file at spec.toml"]

    def test_an_output_path_that_is_not_a_directory_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(target="not_directory"))

        assert [str(text) for text in tree.problems()] == ["the output path is not a directory"]

    def test_a_file_the_tree_does_not_write_is_kept_beside_it(self) -> None:
        tree = domain.Tree(tree_spec(target="occupied", existing=(("README.md", "# voice\n"),)))

        assert (tree.health(), [str(generated_file.path()) for generated_file in tree.files()]) == (
            domain.Health.CLEAN,
            ["calls/domain/call.py"],
        )

    def test_a_file_the_tree_writes_the_same_is_not_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(target="occupied", existing=(("calls/domain/call.py", "class Call:\n"),)))

        assert tree.health() == domain.Health.CLEAN

    def test_a_file_the_tree_would_write_differently_is_a_problem_and_nothing_is_written(self) -> None:
        tree = domain.Tree(tree_spec(target="occupied", existing=(("calls/domain/call.py", "class Other:\n"),)))

        assert ([str(text) for text in tree.problems()], tree.files()) == (
            ["the output directory already has calls/domain/call.py, which the generator would write differently"],
            (),
        )

    def test_an_operation_named_twice_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(write_operation_name="record_call", action_operation_name="record_call"))

        assert [str(text) for text in tree.problems()] == [
            "operation 'record_call' is named twice; every operation has a name of its own"
        ]

    def test_an_operation_with_a_relay_prefix_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(write_operation_name="start_call"))

        assert [str(text) for text in tree.problems()] == [
            "operation 'start_call' starts with 'start_', a prefix the analyzer reserves for "
            "relay operations (TB085); name the operation without it"
        ]

    def test_an_operation_of_one_word_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(write_operation_name="place"))

        assert [str(text) for text in tree.problems()] == [
            "client.write_operation_name 'place' is not a snake_case verb and noun, like place_call"
        ]

    def test_a_field_type_without_templates_is_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(aggregate_fields=(("person_name", "float"), ("phone_number", "str"))))

        assert [str(text) for text in tree.problems()] == [
            "aggregate_fields names 'person_name' as 'float'; a field is one of str, int"
        ]

    def test_sample_values_of_the_wrong_type_are_a_problem(self) -> None:
        tree = domain.Tree(
            tree_spec(
                aggregate_fields=(("person_name", "str"), ("phone_number", "str")),
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("int", "1"), ("int", "2"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
            )
        )

        assert [str(text) for text in tree.problems()] == [
            "sample_values for 'person_name' holds a value that is not a str"
        ]

    def test_a_sample_value_carrying_a_quote_is_a_problem(self) -> None:
        tree = domain.Tree(
            tree_spec(
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("str", 'O"Brien'), ("str", "Grace"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
            )
        )

        assert [str(text) for text in tree.problems()] == [
            "sample value 'O\"Brien' for 'person_name' is not printable ASCII free of quotes and backslashes"
        ]

    def test_sample_values_that_repeat_are_a_problem(self) -> None:
        tree = domain.Tree(
            tree_spec(
                sample_values=(
                    ("call_id", (("str", "call-1"), ("str", "call-2"))),
                    ("person_name", (("str", "Ada"), ("str", "Ada"))),
                    ("phone_number", (("str", "+15555550100"), ("str", "+15555550101"))),
                ),
            )
        )

        assert [str(text) for text in tree.problems()] == [
            "sample_values for 'person_name' repeats a value; its values differ"
        ]

    def test_an_assertion_on_a_field_the_read_does_not_answer_is_a_problem(self) -> None:
        tree = domain.Tree(
            tree_spec(read_response_fields=("call_id", "person_name"), asserted_field="phone_number")
        )

        assert [str(text) for text in tree.problems()] == [
            "acceptance_test.asserted_field 'phone_number' is not an aggregate field the client read answers"
        ]

    def test_random_values_of_the_wrong_type_are_a_problem(self) -> None:
        tree = domain.Tree(tree_spec(asserted_field="person_name", random_values=(("int", "3"),)))

        assert [str(text) for text in tree.problems()] == [
            "acceptance_test.random_values holds a value that is not a str"
        ]


class TestGenerationPaths:

    def test_the_paths_come_back_as_they_were_given(self) -> None:
        generation_paths = domain.GenerationPaths(
            domain.GenerationPathsSpec(spec_path="specs/voice.toml", out_dir="/tmp/voice")
        )

        assert (str(generation_paths.spec_path()), str(generation_paths.out_dir())) == (
            "specs/voice.toml",
            "/tmp/voice",
        )
