from __future__ import annotations

import enum
import re
import typing

import tesser.domain as ts

import tesser.serialization as serialization

READ: typing.Final[str] = "read"

MISSING: typing.Final[str] = "missing"

UNREADABLE: typing.Final[str] = "unreadable"

MALFORMED: typing.Final[str] = "malformed"

NOT_DIRECTORY: typing.Final[str] = "not_directory"

ENGINE: typing.Final[str] = "restate"

STORAGES: typing.Final[tuple[str, ...]] = ("postgres", "memory")

HOSTS: typing.Final[tuple[str, ...]] = ("cli", "http")

CALLING_MODES: typing.Final[tuple[str, ...]] = ("run", "start")

IDENTITY_TYPE: typing.Final[str] = "str"

SAMPLE_COUNT: typing.Final[int] = 2

TYPES: typing.Final[dict[str, tuple[str, str, str, str, str]]] = {
    "str": ("text", "canonical_str", "__str__", "arg", "text"),
    "int": ("bigint", "canonical_int", "__int__", "int_arg", "integer"),
}

RELAY_PREFIXES: typing.Final[tuple[str, ...]] = ("start_", "run_", "await_")

RESERVED: typing.Final[frozenset[str]] = frozenset(
    {
        "adapters",
        "app",
        "application",
        "client",
        "component",
        "config",
        "conftest",
        "domain",
        "identity",
        "pgdatabase",
        "protocol",
        "spec",
        "srv",
        "tests",
    }
)

SNAKE: typing.Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")

OPERATION: typing.Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")

PASCAL: typing.Final[re.Pattern[str]] = re.compile(r"(?:[A-Z][a-z0-9]+)+")

ENVIRONMENT: typing.Final[re.Pattern[str]] = re.compile(r"[A-Z][A-Z0-9_]*")

TEST_CLASS: typing.Final[re.Pattern[str]] = re.compile(r"Test(?:[A-Z][a-z0-9]*)+")

TEST_METHOD: typing.Final[re.Pattern[str]] = re.compile(r"test(?:_[a-z0-9]+)+")

SAMPLE_TEXT: typing.Final[re.Pattern[str]] = re.compile(r"[ !#-&(-\[\]-~]+")

IDENTITY_TEXT: typing.Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9._~-]+")

WORD_START: typing.Final[re.Pattern[str]] = re.compile(r"(?<!^)(?=[A-Z])")

TAG: typing.Final[re.Pattern[str]] = re.compile(r"\{\{([#^/]?)([A-Za-z_][A-Za-z0-9_]*)\}\}")

GUARD: typing.Final[re.Pattern[str]] = re.compile(r"\{\{([#^])([A-Za-z_][A-Za-z0-9_]*)\}\}")

TEMPLATE_SUFFIX: typing.Final[str] = ".tmpl"


class Health(ts.Outcome):

    CLEAN = enum.auto()
    PROBLEMS = enum.auto()


class Text(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class ScopeSpec(ts.Spec):

    def __init__(
        self,
        values: tuple[tuple[str, str], ...],
        sections: tuple[tuple[str, tuple[tuple[tuple[str, str], ...], ...]], ...],
    ) -> None:
        self.values = values
        self.sections = sections


class Scope(ts.ValueObject):

    _bindings: tuple[
        tuple[tuple[str, str], ...],
        tuple[tuple[str, tuple[tuple[tuple[str, str], ...], ...]], ...],
    ]

    def __init__(self, spec: ScopeSpec) -> None:
        object.__setattr__(self, "_bindings", (spec.values, spec.sections))

    def value(self, name: str) -> Text:
        values, _ = self._bindings
        for key, bound in values:
            if key == name:
                return Text(bound)
        raise ValueError(f"a template names {{{{{name}}}}}, which the spec binds to nothing")

    def enter(self, name: str) -> tuple[Scope, ...]:
        values, sections = self._bindings
        listed = dict(sections)
        if name in listed:
            return tuple(Scope(ScopeSpec(values=item + values, sections=sections)) for item in listed[name])
        for key, bound in values:
            if key == name:
                return (self,) if bound else ()
        raise ValueError(f"a template opens {{{{#{name}}}}}, which the spec binds to nothing")

    def skip(self, name: str) -> tuple[Scope, ...]:
        values, sections = self._bindings
        listed = dict(sections)
        if name in listed:
            return () if listed[name] else (self,)
        for key, bound in values:
            if key == name:
                return () if bound else (self,)
        raise ValueError(f"a template opens {{{{^{name}}}}}, which the spec binds to nothing")


class Template(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)

    def place(self, scope: Scope) -> tuple[Text, ...]:
        kept: list[str] = []
        for segment in self._value.split("/"):
            guard = GUARD.fullmatch(segment)
            if guard is None:
                kept.append(segment)
                continue
            opened = scope.enter(guard.group(2)) if guard.group(1) == "#" else scope.skip(guard.group(2))
            if not opened:
                return ()
        return (Template("/".join(kept)).render(scope),)

    def render(self, scope: Scope) -> Text:
        text = self._value
        rendered: list[str] = []
        position = 0
        tag = TAG.search(text, position)
        while tag is not None:
            sigil = tag.group(1)
            name = tag.group(2)
            if sigil == "":
                rendered.append(text[position : tag.start()])
                rendered.append(str(scope.value(name)))
                position = tag.end()
                tag = TAG.search(text, position)
                continue
            if sigil == "/":
                raise ValueError(f"a template closes {{{{/{name}}}}} before it opens it")
            depth = 1
            close = TAG.search(text, tag.end())
            while close is not None:
                if close.group(2) == name and close.group(1) in ("#", "^"):
                    depth += 1
                elif close.group(2) == name and close.group(1) == "/":
                    depth -= 1
                    if depth == 0:
                        break
                close = TAG.search(text, close.end())
            if close is None:
                raise ValueError(f"a template never closes {{{{{sigil}{name}}}}}")
            open_start = text.rfind("\n", 0, tag.start()) + 1
            open_stop = text.find("\n", tag.end())
            open_stop = len(text) if open_stop == -1 else open_stop
            open_alone = (
                open_start >= position
                and not text[open_start : tag.start()].strip()
                and not text[tag.end() : open_stop].strip()
            )
            close_start = text.rfind("\n", 0, close.start()) + 1
            close_stop = text.find("\n", close.end())
            close_stop = len(text) if close_stop == -1 else close_stop
            close_alone = (
                close_start >= tag.end()
                and not text[close_start : close.start()].strip()
                and not text[close.end() : close_stop].strip()
            )
            rendered.append(text[position:open_start] if open_alone else text[position : tag.start()])
            inner_start = open_stop + 1 if open_alone else tag.end()
            inner_stop = close_start if close_alone else close.start()
            inner = text[inner_start:inner_stop] if inner_start < inner_stop else ""
            entered = scope.enter(name) if sigil == "#" else scope.skip(name)
            rendered.extend(str(Template(inner).render(each)) for each in entered)
            position = close_stop + 1 if close_alone else close.end()
            tag = TAG.search(text, position)
        rendered.append(text[position:])
        return Text("".join(rendered))


class GeneratedFileSpec(ts.Spec):

    def __init__(self, path: str, content: str) -> None:
        self.path = path
        self.content = content


class GeneratedFile(ts.ValueObject):

    _path: Text
    _content: Text

    def __init__(self, spec: GeneratedFileSpec) -> None:
        object.__setattr__(self, "_path", Text(spec.path))
        object.__setattr__(self, "_content", Text(spec.content))

    def path(self) -> Text:
        return self._path

    def content(self) -> Text:
        return self._content


class GenerationPathsSpec(ts.Spec):

    def __init__(self, spec_path: str, out_dir: str) -> None:
        self.spec_path = spec_path
        self.out_dir = out_dir


class GenerationPaths(ts.ValueObject):

    _spec_path: Text
    _out_dir: Text

    def __init__(self, spec: GenerationPathsSpec) -> None:
        object.__setattr__(self, "_spec_path", Text(spec.spec_path))
        object.__setattr__(self, "_out_dir", Text(spec.out_dir))

    def spec_path(self) -> Text:
        return self._spec_path

    def out_dir(self) -> Text:
        return self._out_dir


class TreeSpec(ts.Spec):

    def __init__(
        self,
        state: str,
        note: str,
        unknown_keys: tuple[str, ...],
        target: str,
        existing: tuple[tuple[str, str], ...],
        printed: tuple[str, ...],
        app_name: str,
        bounded_context_name: str,
        aggregate_root_class_name: str,
        durable_execution_engine: str,
        storage: str,
        host: str,
        identity_field_name: str,
        identity_port_operation_name: str,
        aggregate_fields: tuple[tuple[str, str], ...],
        sample_values: tuple[tuple[str, tuple[tuple[str, str], ...]], ...],
        write_operation_name: str,
        read_operation_name: str,
        read_response_fields: tuple[str, ...],
        orchestrator_operation_name: str,
        orchestrator_calling_mode: str,
        action_operation_name: str,
        save_operation_name: str,
        load_operation_name: str,
        load_response_collection_name: str,
        test_class_name: str,
        test_method_name: str,
        asserted_field: str,
        random_values: tuple[tuple[str, str], ...],
        storage_url_variable: str,
        engine_url_variable: str,
        templates: tuple[tuple[str, str], ...],
    ) -> None:
        self.state = state
        self.note = note
        self.unknown_keys = unknown_keys
        self.target = target
        self.existing = existing
        self.printed = printed
        self.app_name = app_name
        self.bounded_context_name = bounded_context_name
        self.aggregate_root_class_name = aggregate_root_class_name
        self.durable_execution_engine = durable_execution_engine
        self.storage = storage
        self.host = host
        self.identity_field_name = identity_field_name
        self.identity_port_operation_name = identity_port_operation_name
        self.aggregate_fields = aggregate_fields
        self.sample_values = sample_values
        self.write_operation_name = write_operation_name
        self.read_operation_name = read_operation_name
        self.read_response_fields = read_response_fields
        self.orchestrator_operation_name = orchestrator_operation_name
        self.orchestrator_calling_mode = orchestrator_calling_mode
        self.action_operation_name = action_operation_name
        self.save_operation_name = save_operation_name
        self.load_operation_name = load_operation_name
        self.load_response_collection_name = load_response_collection_name
        self.test_class_name = test_class_name
        self.test_method_name = test_method_name
        self.asserted_field = asserted_field
        self.random_values = random_values
        self.storage_url_variable = storage_url_variable
        self.engine_url_variable = engine_url_variable
        self.templates = templates


class Tree(ts.AggregateRoot):

    def __init__(self, spec: TreeSpec) -> None:
        found: list[Text] = []
        identity = spec.identity_field_name
        kinds = {identity: IDENTITY_TYPE, **dict(spec.aggregate_fields)}
        field_names = tuple(name for name, _ in spec.aggregate_fields)
        sampled = dict(spec.sample_values)
        storage = spec.storage or STORAGES[0]
        host = spec.host or HOSTS[0]
        calling_mode = spec.orchestrator_calling_mode or CALLING_MODES[0]
        if spec.state == MISSING:
            found.append(Text(f"there is no spec file at {spec.note}"))
        elif spec.state == UNREADABLE:
            found.append(Text(f"the spec file at {spec.note} is not readable UTF-8 text"))
        elif spec.state == MALFORMED:
            found.append(Text(f"the spec file is not TOML: {spec.note}"))
        elif spec.state != READ:
            found.append(Text(f"the spec file could not be read: {spec.state}"))
        else:
            for unknown in spec.unknown_keys:
                found.append(Text(f"the spec names '{unknown}', which is not a key the spec takes"))
            shaped = (
                ("app_name", spec.app_name, SNAKE, "a snake_case name, like voice"),
                ("bounded_context_name", spec.bounded_context_name, SNAKE, "a snake_case name, like calls"),
                ("aggregate_root_class_name", spec.aggregate_root_class_name, PASCAL, "a PascalCase class name, like Call"),
                ("identity_field_name", identity, SNAKE, "a snake_case field name, like call_id"),
                (
                    "identity_port_operation_name",
                    spec.identity_port_operation_name,
                    OPERATION,
                    "a snake_case verb and noun, like issue_call_id",
                ),
                ("client.write_operation_name", spec.write_operation_name, OPERATION, "a snake_case verb and noun, like place_call"),
                ("client.read_operation_name", spec.read_operation_name, OPERATION, "a snake_case verb and noun, like get_call"),
                (
                    "orchestrator.operation_name",
                    spec.orchestrator_operation_name,
                    OPERATION,
                    "a snake_case verb and noun, like conduct_call",
                ),
                ("action.operation_name", spec.action_operation_name, OPERATION, "a snake_case verb and noun, like record_call"),
                ("repository.save_operation_name", spec.save_operation_name, OPERATION, "a snake_case verb and noun, like save_call"),
                ("repository.load_operation_name", spec.load_operation_name, OPERATION, "a snake_case verb and noun, like load_call"),
                (
                    "repository.load_response_collection_name",
                    spec.load_response_collection_name,
                    SNAKE,
                    "a snake_case name, like calls",
                ),
                (
                    "acceptance_test.test_class_name",
                    spec.test_class_name,
                    TEST_CLASS,
                    "a Test-prefixed PascalCase class name, like TestPlacingCalls",
                ),
                (
                    "acceptance_test.test_method_name",
                    spec.test_method_name,
                    TEST_METHOD,
                    "a test_-prefixed snake_case method name, like test_a_call_is_successfully_made",
                ),
                ("acceptance_test.asserted_field", spec.asserted_field, SNAKE, "a snake_case field name"),
                (
                    "environment_variables.engine_url",
                    spec.engine_url_variable,
                    ENVIRONMENT,
                    "an upper-case environment variable name",
                ),
            )
            stated_variables = (
                ("environment_variables.storage_url", spec.storage_url_variable, storage == "postgres", "a postgres store"),
            )
            for key, value, shape, described in shaped:
                if not value:
                    found.append(Text(f"the spec names no {key}"))
                elif shape.fullmatch(value) is None:
                    found.append(Text(f"{key} '{value}' is not {described}"))
            for key, value, needed, reader in stated_variables:
                if needed and not value:
                    found.append(Text(f"the spec names no {key}, which {reader} reads"))
                elif not needed and value:
                    found.append(Text(f"the spec names {key}, which only {reader} reads"))
                elif value and ENVIRONMENT.fullmatch(value) is None:
                    found.append(Text(f"{key} '{value}' is not an upper-case environment variable name"))
            if spec.durable_execution_engine != ENGINE:
                found.append(
                    Text(
                        f"durable_execution_engine '{spec.durable_execution_engine}' has no templates; "
                        f"the one engine is '{ENGINE}'"
                    )
                )
            if storage not in STORAGES:
                found.append(Text(f"storage '{storage}' has no templates; a storage is one of {', '.join(STORAGES)}"))
            if host not in HOSTS:
                found.append(Text(f"host '{host}' has no templates; a host is one of {', '.join(HOSTS)}"))
            if calling_mode not in CALLING_MODES:
                found.append(
                    Text(
                        f"orchestrator.calling_mode '{calling_mode}' has no templates; "
                        f"a calling mode is one of {', '.join(CALLING_MODES)}"
                    )
                )
            if storage == "memory" and host == "cli":
                found.append(
                    Text(
                        "storage 'memory' needs host 'http': a cli host reads in a process of its own, "
                        "so it never sees the store the served Restate endpoint writes"
                    )
                )
            if spec.bounded_context_name in RESERVED:
                found.append(
                    Text(f"bounded_context_name '{spec.bounded_context_name}' is a name the generated tree already uses")
                )
            if not spec.aggregate_fields:
                found.append(Text("aggregate_fields names no fields"))
            identity_class = "".join(part.capitalize() for part in identity.split("_"))
            taken = {spec.aggregate_root_class_name, identity_class, f"{spec.aggregate_root_class_name}Spec"}
            for name, kind in spec.aggregate_fields:
                if SNAKE.fullmatch(name) is None:
                    found.append(Text(f"aggregate_fields names '{name}', which is not a snake_case name"))
                if name == identity:
                    found.append(Text(f"aggregate_fields names '{name}', which is the identity field"))
                if name in RESERVED:
                    found.append(Text(f"aggregate_fields names '{name}', a name the generated tree already uses"))
                if kind not in TYPES:
                    found.append(Text(f"aggregate_fields names '{name}' as '{kind}'; a field is one of {', '.join(TYPES)}"))
                if "".join(part.capitalize() for part in name.split("_")) in taken:
                    found.append(Text(f"aggregate_fields names '{name}', whose class the domain module already declares"))
            for name in sampled:
                if name not in kinds:
                    found.append(
                        Text(f"sample_values names '{name}', which is neither the identity field nor an aggregate field")
                    )
            for name, kind in kinds.items():
                if name not in sampled:
                    found.append(Text(f"sample_values names no values for '{name}'"))
                    continue
                values = sampled[name]
                if len(values) != SAMPLE_COUNT:
                    found.append(
                        Text(f"sample_values for '{name}' holds {len(values)} values; each field takes {SAMPLE_COUNT}")
                    )
                if len({text for _, text in values}) != len(values):
                    found.append(Text(f"sample_values for '{name}' repeats a value; its values differ"))
                if kind in TYPES and any(value_kind != kind for value_kind, _ in values):
                    found.append(Text(f"sample_values for '{name}' holds a value that is not a {kind}"))
                for value_kind, text in values:
                    if value_kind == "str" and SAMPLE_TEXT.fullmatch(text) is None:
                        found.append(
                            Text(f"sample value '{text}' for '{name}' is not printable ASCII free of quotes and backslashes")
                        )
                    elif name == identity and IDENTITY_TEXT.fullmatch(text) is None:
                        found.append(
                            Text(f"sample value '{text}' for '{name}' is not letters, digits, '.', '_', '~', and '-'")
                        )
            if not spec.read_response_fields:
                found.append(Text("client.read_response_fields names no fields"))
            for answer in spec.read_response_fields:
                if answer not in kinds:
                    found.append(
                        Text(
                            f"client.read_response_fields names '{answer}', "
                            f"which is neither the identity field nor an aggregate field"
                        )
                    )
            for answer in sorted({answer for answer in spec.read_response_fields if spec.read_response_fields.count(answer) > 1}):
                found.append(Text(f"client.read_response_fields names '{answer}' twice"))
            if spec.asserted_field and (
                spec.asserted_field == identity or spec.asserted_field not in spec.read_response_fields
            ):
                found.append(
                    Text(
                        f"acceptance_test.asserted_field '{spec.asserted_field}' "
                        f"is not an aggregate field the client read answers"
                    )
                )
            if not spec.random_values:
                found.append(Text("acceptance_test.random_values names no values"))
            asserted_kind = kinds.get(spec.asserted_field, "")
            if asserted_kind in TYPES and any(value_kind != asserted_kind for value_kind, _ in spec.random_values):
                found.append(Text(f"acceptance_test.random_values holds a value that is not a {asserted_kind}"))
            for value_kind, text in spec.random_values:
                if value_kind == "str" and SAMPLE_TEXT.fullmatch(text) is None:
                    found.append(
                        Text(f"random value '{text}' is not printable ASCII free of quotes and backslashes")
                    )
            operations = [
                spec.write_operation_name,
                spec.read_operation_name,
                spec.orchestrator_operation_name,
                spec.action_operation_name,
                spec.save_operation_name,
                spec.load_operation_name,
                spec.identity_port_operation_name,
            ]
            for operation in sorted({operation for operation in operations if operation and operations.count(operation) > 1}):
                found.append(Text(f"operation '{operation}' is named twice; every operation has a name of its own"))
            for operation in operations:
                prefix = next((prefix for prefix in RELAY_PREFIXES if operation.startswith(prefix)), None)
                if prefix is not None:
                    found.append(
                        Text(
                            f"operation '{operation}' starts with '{prefix}', a prefix the analyzer reserves for "
                            f"relay operations (TB085); name the operation without it"
                        )
                    )
            if spec.target == NOT_DIRECTORY:
                found.append(Text("the output path is not a directory"))
            if not spec.templates:
                found.append(Text("no templates were found"))
        if found:
            self._problems = tuple(found)
            self._files: tuple[GeneratedFile, ...] = ()
            self._printed: tuple[GeneratedFile, ...] = ()
            return
        classes = {
            name: "".join(part.capitalize() for part in name.split("_"))
            for name in (
                spec.app_name,
                spec.bounded_context_name,
                identity,
                spec.write_operation_name,
                spec.read_operation_name,
                spec.orchestrator_operation_name,
                spec.action_operation_name,
                spec.save_operation_name,
                spec.load_operation_name,
                spec.identity_port_operation_name,
                *field_names,
            )
        }
        literals = {
            name: tuple(f'"{text}"' if value_kind == "str" else text for value_kind, text in values)
            for name, values in sampled.items()
        }
        items: dict[str, tuple[tuple[str, str], ...]] = {}
        for name, kind in kinds.items():
            sql_type, canonical, dunder, cli_arg, http_arg = TYPES[kind]
            items[name] = (
                ("field", name),
                ("Field", classes[name]),
                ("py_type", kind),
                ("sql_type", sql_type),
                ("canonical", canonical),
                ("dunder", dunder),
                ("cli_arg", cli_arg),
                ("http_arg", http_arg),
                ("sample", literals[name][0]),
                ("sample2", literals[name][1]),
                ("sample_arg", f'"{sampled[name][0][1]}"'),
                ("wrong", "1" if kind == "str" else '"1"'),
                ("accessor", "identity" if name == identity else name),
                ("is_identity", "true" if name == identity else ""),
                ("is_asserted", "true" if name == spec.asserted_field else ""),
            )
        listed = (
            ("fields", field_names),
            ("record_fields", (identity, *field_names)),
            ("read_fields", spec.read_response_fields),
        )
        sections = tuple(
            (
                section,
                tuple(
                    items[name]
                    + (
                        ("comma", ", " if index < len(names) - 1 else ""),
                        (
                            "prose",
                            ""
                            if index == 0
                            else (" and " if len(names) == 2 else (", and " if index == len(names) - 1 else ", ")),
                        ),
                        ("position", str(index + 1)),
                        ("index", str(index)),
                    )
                    for index, name in enumerate(names)
                ),
            )
            for section, names in listed
        )
        choices = tuple(f'"{text}"' if value_kind == "str" else text for value_kind, text in spec.random_values)
        values = (
            ("app", spec.app_name),
            ("App", classes[spec.app_name]),
            ("context", spec.bounded_context_name),
            ("Context", classes[spec.bounded_context_name]),
            ("aggregate", WORD_START.sub("_", spec.aggregate_root_class_name).lower()),
            ("Aggregate", spec.aggregate_root_class_name),
            ("identity", identity),
            ("Identity", classes[identity]),
            ("identity_sample", literals[identity][0]),
            ("identity_sample2", literals[identity][1]),
            ("identity_raw", sampled[identity][0][1]),
            ("write", spec.write_operation_name),
            ("Write", classes[spec.write_operation_name]),
            ("read", spec.read_operation_name),
            ("Read", classes[spec.read_operation_name]),
            ("conduct", spec.orchestrator_operation_name),
            ("Conduct", classes[spec.orchestrator_operation_name]),
            ("conduct_words", spec.orchestrator_operation_name.replace("_", " ")),
            ("record", spec.action_operation_name),
            ("Record", classes[spec.action_operation_name]),
            ("record_words", spec.action_operation_name.replace("_", " ")),
            ("save", spec.save_operation_name),
            ("Save", classes[spec.save_operation_name]),
            ("load", spec.load_operation_name),
            ("Load", classes[spec.load_operation_name]),
            ("issue", spec.identity_port_operation_name),
            ("Issue", classes[spec.identity_port_operation_name]),
            ("collection", spec.load_response_collection_name),
            ("storage_env", spec.storage_url_variable),
            ("engine_url_env", spec.engine_url_variable),
            ("storage", storage),
            ("storage_postgres", "true" if storage == "postgres" else ""),
            ("storage_memory", "true" if storage == "memory" else ""),
            ("host_cli", "true" if host == "cli" else ""),
            ("host_http", "true" if host == "http" else ""),
            ("calling_run", "true" if calling_mode == "run" else ""),
            ("calling_start", "true" if calling_mode == "start" else ""),
            ("asserts", spec.asserted_field),
            ("field_count", str(len(field_names))),
            ("random_choices", "(" + ", ".join(choices) + ("," if len(choices) == 1 else "") + ")"),
            ("test_class", spec.test_class_name),
            ("test_method", spec.test_method_name),
        )
        scope = Scope(ScopeSpec(values=values, sections=sections))
        rendered = tuple(
            sorted(
                (
                    GeneratedFile(
                        GeneratedFileSpec(
                            path=str(placed).removesuffix(TEMPLATE_SUFFIX),
                            content=str(Template(text).render(scope)),
                        )
                    )
                    for path, text in spec.templates
                    for placed in Template(path).place(scope)
                ),
                key=str,
            )
        )
        existing = dict(spec.existing)
        written = {str(generated_file.path()): generated_file for generated_file in rendered}
        self._problems = tuple(
            Text(f"the output directory already has {generated_file.path()}, which the generator would write differently")
            for generated_file in rendered
            if existing.get(str(generated_file.path()), str(generated_file.content())) != str(generated_file.content())
        ) + tuple(
            Text(f"--print names {path}, which the generator does not write")
            for path in spec.printed
            if path not in written
        )
        self._files = () if self._problems else rendered
        self._printed = () if self._problems else tuple(written[path] for path in spec.printed)

    def health(self) -> Health:
        return Health.PROBLEMS if self._problems else Health.CLEAN

    def problems(self) -> tuple[Text, ...]:
        return self._problems

    def files(self) -> tuple[GeneratedFile, ...]:
        return self._files

    def printed(self) -> tuple[GeneratedFile, ...]:
        return self._printed
