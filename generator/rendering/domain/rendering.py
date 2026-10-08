from __future__ import annotations

import ast
import enum
import hashlib
import json
import keyword
import re
import tomllib
import typing

import tesser.domain as ts

import tesser.serialization as serialization

TAG: typing.Final[re.Pattern[str]] = re.compile(r"\{\{([#^/]?)([A-Za-z_][A-Za-z0-9_]*)\}\}")

GUARD: typing.Final[re.Pattern[str]] = re.compile(r"\{\{([#^])([A-Za-z_][A-Za-z0-9_]*)\}\}")

TEMPLATE_SUFFIX: typing.Final[str] = ".tmpl"

AGENT_MARKER: typing.Final[str] = "# pragma: tesser-agent-owned;"

GENERATED_MARKER: typing.Final[str] = "# pragma: tesser-generated;"
RENDERED_FROM: typing.Final[str] = ".tesser-rendered"

SNAKE: typing.Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")

OPERATION: typing.Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")

PASCAL: typing.Final[re.Pattern[str]] = re.compile(r"(?:[A-Z][a-z0-9]+)+")

VARIABLE: typing.Final[re.Pattern[str]] = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*")

ENGINE_PATH: typing.Final[re.Pattern[str]] = re.compile(r"/[a-z0-9_-]+(?:/[a-z0-9_-]+)*")

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

PATTERNS: typing.Final[dict[str, tuple[re.Pattern[str], str]]] = {
    "snake": (SNAKE, "snake_case name, like loan_id"),
    "operation": (OPERATION, "snake_case operation of at least two words, like lend_book"),
    "pascal": (PASCAL, "PascalCase name, like LoanRepository"),
    "variable": (VARIABLE, "UPPER_CASE variable, like RESTATE_URL"),
    "path": (ENGINE_PATH, "URL path of lowercase segments, like /restate"),
}

DOCUMENTS: typing.Final[tuple[str, ...]] = ("language", "story", "infra", "composition", "implementations", "generator")

HOLDS: typing.Final[dict[str, str]] = {"infra": "what the app runs on and what an operator must provide"}

MOVED_TO_INFRA: typing.Final[tuple[tuple[str, str], ...]] = (
    ("app", "app"), ("engine", "[engine]"), ("hosts", "[hosts]"), ("variables", "[variables]"),
)

READ: typing.Final[str] = "read"

ROUTE: typing.Final[re.Pattern[str]] = re.compile(r"(GET|POST|PUT|PATCH|DELETE) (/(?:[a-z0-9_-]+|\{[a-z][a-z0-9_]*\})(?:/(?:[a-z0-9_-]+|\{[a-z][a-z0-9_]*\}))*)")

PATH_FIELD: typing.Final[re.Pattern[str]] = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
GERUNDS: typing.Final[dict[str, str]] = {
    "GET": "reading", "POST": "submitting", "PUT": "replacing", "PATCH": "updating", "DELETE": "deleting",
}

WORD_START: typing.Final[re.Pattern[str]] = re.compile(r"(?<!^)(?=[A-Z])")

PRIMITIVE_TYPES: typing.Final[tuple[str, ...]] = ("str", "int")

UNKNOWN: typing.Final[str] = "\x00unknown"

WHOLE: typing.Final[str] = "*"

NESTED: typing.Final[str] = " / "

RECORDED: typing.Final[str] = "recorded"

GENERATED: typing.Final[str] = "generated"

OWNED: typing.Final[str] = "owned"


class Health(ts.Outcome):

    CLEAN = enum.auto()
    PROBLEMS = enum.auto()


class Text(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Word(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)

    def pascal(self) -> Word:
        return Word("".join(part[:1].upper() + part[1:] for part in self._value.split("_")))

    def snake(self) -> Word:
        return Word(WORD_START.sub("_", self._value).lower())

    def singular(self) -> Word:
        if self._value.endswith("ies"):
            return Word(self._value[:-3] + "y")
        if self._value.endswith("s"):
            return Word(self._value[:-1])
        return self

    def plural(self) -> Word:
        return Word(self._value + "s")

    def upper(self) -> Word:
        return Word(self._value.upper())

    def spaced(self) -> Word:
        return Word(self._value.replace("_", " "))


class Scope(ts.ValueObject):

    _value: tuple[tuple[str, ...], tuple[int, ...]]

    def __init__(self, value: tuple[tuple[str, ...], tuple[int, ...]]) -> None:
        object.__setattr__(self, "_value", value)

    def value(self, name: str) -> Text:
        table, stack = self._value
        for index in stack:
            frame = json.loads(table[index])
            if name not in frame:
                continue
            if isinstance(frame[name], str):
                return Text(frame[name])
            raise ValueError(f"a template names {{{{{name}}}}}, which is a section, not a value")
        raise ValueError(f"a template names {{{{{name}}}}}, which nothing binds")

    def enter(self, name: str) -> tuple[Scope, ...]:
        table, stack = self._value
        for index in stack:
            frame = json.loads(table[index])
            if name not in frame:
                continue
            if isinstance(frame[name], list):
                return tuple(Scope((table, (int(child),) + stack)) for child in frame[name])
            raise ValueError(f"a template opens {{{{#{name}}}}}, which is a value, not a section")
        raise ValueError(f"a template opens {{{{#{name}}}}}, which nothing binds")

    def skip(self, name: str) -> tuple[Scope, ...]:
        table, stack = self._value
        for index in stack:
            frame = json.loads(table[index])
            if name not in frame:
                continue
            if isinstance(frame[name], list):
                return () if frame[name] else (self,)
            raise ValueError(f"a template opens {{{{^{name}}}}}, which is a value, not a section")
        raise ValueError(f"a template opens {{{{^{name}}}}}, which nothing binds")


class Template(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)

    def place(self, scope: Scope) -> tuple[Scope, ...]:
        segments = self._value.split("/")
        for index, segment in enumerate(segments):
            guard = GUARD.fullmatch(segment)
            if guard is None:
                continue
            template = Template("/".join(segments[:index] + segments[index + 1:]))
            opened = scope.enter(guard.group(2)) if guard.group(1) == "#" else scope.skip(guard.group(2))
            return tuple(placed for each in opened for placed in template.place(each))
        return (scope,)

    def unguarded(self) -> Template:
        return Template("/".join(segment for segment in self._value.split("/") if GUARD.fullmatch(segment) is None))

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


class Pairs(ts.ValueObject):

    _value: tuple[tuple[str, str], ...]

    def __init__(self, value: tuple[tuple[str, str], ...]) -> None:
        object.__setattr__(self, "_value", value)

    def __iter__(self) -> typing.Iterator[tuple[str, str]]:
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def get(self, name: str) -> Text | None:
        for key, bound in self._value:
            if key == name:
                return Text(bound)
        return None


class TypesSpec(ts.Spec):

    def __init__(
        self,
        enums: tuple[tuple[str, tuple[str, ...]], ...],
        shapes: tuple[tuple[str, tuple[tuple[str, str], ...]], ...],
        aggregate: str,
        aggregate_fields: tuple[tuple[str, str], ...],
    ) -> None:
        self.enums = enums
        self.shapes = shapes
        self.aggregate = aggregate
        self.aggregate_fields = aggregate_fields


class Types(ts.ValueObject):

    _rows: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]

    def __init__(self, spec: TypesSpec) -> None:
        rows = [(name, "enum", tuple((member, member) for member in members)) for name, members in spec.enums]
        rows.extend((name, "shape", fields) for name, fields in spec.shapes)
        rows.append((spec.aggregate, "aggregate", spec.aggregate_fields))
        object.__setattr__(self, "_rows", tuple(rows))

    def kind(self, type_text: str) -> Word:
        if type_text.endswith("[]"):
            return Word("array")
        if type_text in PRIMITIVE_TYPES:
            return Word("scalar")
        for name, kind, _ in self._rows:
            if name == type_text:
                return Word(kind)
        raise ValueError(f"a field is typed {type_text}, which is neither str, int, an enum, a shape, nor the aggregate")

    def element(self, type_text: str) -> Word:
        return Word(type_text.removesuffix("[]"))

    def fields(self, shape: str) -> Pairs:
        for name, kind, items in self._rows:
            if name == shape and kind in ("shape", "aggregate"):
                return Pairs(items)
        raise ValueError(f"{shape} is named as a shape, and no [shapes] or [messages] table declares it")

    def members(self, enum: str) -> Pairs:
        for name, kind, items in self._rows:
            if name == enum and kind == "enum":
                return Pairs(items)
        raise ValueError(f"{enum} is named as an enum, and [enums] does not declare it")


class TargetSpec(ts.Spec):

    def __init__(
        self,
        field: str,
        type_text: str,
        kind: str,
        package: str,
        record: str,
        element: tuple[tuple[str, str], ...],
        members: tuple[TargetSpec, ...],
    ) -> None:
        self.field = field
        self.type_text = type_text
        self.kind = kind
        self.package = package
        self.record = record
        self.element = element
        self.members = members


class Target(ts.ValueObject):

    _field: Word
    _type_text: Word
    _kind: Word
    _package: Word
    _record: Word
    _element: Pairs
    _members: tuple[Target, ...]

    def __init__(self, spec: TargetSpec) -> None:
        object.__setattr__(self, "_field", Word(spec.field))
        object.__setattr__(self, "_type_text", Word(spec.type_text))
        object.__setattr__(self, "_kind", Word(spec.kind))
        object.__setattr__(self, "_package", Word(spec.package))
        object.__setattr__(self, "_record", Word(spec.record))
        object.__setattr__(self, "_element", Pairs(spec.element))
        object.__setattr__(self, "_members", tuple(Target(member) for member in spec.members))

    def field(self) -> Word:
        return self._field

    def type_text(self) -> Word:
        return self._type_text

    def kind(self) -> Word:
        return self._kind

    def package(self) -> Word:
        return self._package

    def record(self) -> Word:
        return self._record

    def element(self) -> Pairs:
        return self._element

    def members(self) -> tuple[Target, ...]:
        return self._members


class SourceSpec(ts.Spec):

    def __init__(self, expr: str, type_ref: str, kind: str, prefix: str, holds: tuple[tuple[str, str], ...]) -> None:
        self.expr = expr
        self.type_ref = type_ref
        self.kind = kind
        self.prefix = prefix
        self.holds = holds


class Source(ts.ValueObject):

    _expr: Word
    _type_ref: Word
    _kind: Word
    _prefix: Word
    _holds: Pairs

    def __init__(self, spec: SourceSpec) -> None:
        object.__setattr__(self, "_expr", Word(spec.expr))
        object.__setattr__(self, "_type_ref", Word(spec.type_ref))
        object.__setattr__(self, "_kind", Word(spec.kind))
        object.__setattr__(self, "_prefix", Word(spec.prefix))
        object.__setattr__(self, "_holds", Pairs(spec.holds))

    def expr(self) -> Word:
        return self._expr

    def type_ref(self) -> Word:
        return self._type_ref

    def kind(self) -> Word:
        return self._kind

    def prefix(self) -> Word:
        return self._prefix

    def holds(self) -> Pairs:
        return self._holds


class SourcesSpec(ts.Spec):

    def __init__(self, name: str) -> None:
        self.name = name


class Sources(ts.Entity):

    def __init__(self, spec: SourcesSpec) -> None:
        self._name = spec.name
        self._held: list[Source] = []

    @property
    def identity(self) -> str:
        return self._name

    def hold(self, source: Source) -> None:
        self._held.append(source)

    def held(self) -> tuple[Source, ...]:
        return tuple(self._held)

    def find(self, word: Word) -> Source | None:
        for source in reversed(self._held):
            if source.holds().get(str(word)) is not None:
                return source
        return None


class AskSpec(ts.Spec):

    def __init__(self, name: str, target_ref: str, allow_empty: bool, occasion: str = "") -> None:
        self.name = name
        self.target_ref = target_ref
        self.allow_empty = allow_empty
        self.occasion = occasion


class Ask(ts.Entity):

    def __init__(self, spec: AskSpec) -> None:
        self._name = spec.name
        self._occasion = spec.occasion
        self._target_ref = spec.target_ref
        self._allow_empty = spec.allow_empty
        self._targets: list[Target] = []
        self._sources = Sources(SourcesSpec(name=spec.name))

    @property
    def identity(self) -> str:
        return self._name

    def target(self, target: Target) -> None:
        self._targets.append(target)

    def source(self, source: Source) -> None:
        self._sources.hold(source)

    def name(self) -> Word:
        return Word(self._name)

    def occasion(self) -> Word:
        return Word(self._occasion)

    def target_ref(self) -> Word:
        return Word(self._target_ref)

    def empties(self) -> tuple[Word, ...]:
        return (Word("()"),) if self._allow_empty else ()

    def targets(self) -> tuple[Target, ...]:
        return tuple(self._targets)

    def sources(self) -> Sources:
        return self._sources


class MapperDefSpec(ts.Spec):

    def __init__(self, name: str, target: str, params: tuple[tuple[str, str], ...], args: tuple[tuple[str, str], ...]) -> None:
        self.name = name
        self.target = target
        self.params = params
        self.args = args


class MapperDef(ts.ValueObject):

    _name: Word
    _target: Word
    _params: Pairs
    _args: Pairs

    def __init__(self, spec: MapperDefSpec) -> None:
        object.__setattr__(self, "_name", Word(spec.name))
        object.__setattr__(self, "_target", Word(spec.target))
        object.__setattr__(self, "_params", Pairs(spec.params))
        object.__setattr__(self, "_args", Pairs(spec.args))

    def name(self) -> Word:
        return self._name

    def target(self) -> Word:
        return self._target

    def params(self) -> Pairs:
        return self._params

    def args(self) -> Pairs:
        return self._args


class MappedSpec(ts.Spec):

    def __init__(self, call: str, values: tuple[tuple[str, str], ...]) -> None:
        self.call = call
        self.values = values


class Mapped(ts.ValueObject):

    _call: Text
    _values: Pairs

    def __init__(self, spec: MappedSpec) -> None:
        object.__setattr__(self, "_call", Text(spec.call))
        object.__setattr__(self, "_values", Pairs(spec.values))

    def call(self) -> Text:
        return self._call

    def values(self) -> Pairs:
        return self._values


class MappersSpec(ts.Spec):

    def __init__(self, module: str) -> None:
        self.module = module


class Mappers(ts.Entity):

    def __init__(self, spec: MappersSpec) -> None:
        self._module = spec.module
        self._defs: list[MapperDef] = []

    @property
    def identity(self) -> str:
        return self._module

    def defs(self) -> tuple[MapperDef, ...]:
        return tuple(self._defs)

    def map(self, ask: Ask) -> Mapped:
        sources = ask.sources()
        used: list[Source] = []
        args: list[tuple[str, str]] = []
        values: list[tuple[str, str]] = []
        name = str(ask.name())
        for target in ask.targets():
            field = str(target.field())
            kind = str(target.kind())
            package = str(target.package())
            found = sources.find(target.field())
            if found is None:
                if ask.empties() and kind == "array":
                    args.append((field, "()"))
                    values.append((field, "[]"))
                    continue
                raise ValueError(f"{name} needs {field}, and nothing before it in the steps holds one")
            if found not in used:
                used.append(found)
            read = str(found.prefix()) + field
            held = str(found.holds().get(field))
            reads_aggregate = str(found.kind()) == "aggregate"
            if kind == "aggregate":
                if not reads_aggregate:
                    raise ValueError(f"{name} fills {field}, the aggregate itself, from something that is not the aggregate")
                nested = Ask(AskSpec(name=f"MapTo{target.record()}", target_ref=f"ports.{target.record()}", allow_empty=False,
                                     occasion=str(ask.occasion())))
                for member in target.members():
                    nested.target(member)
                nested.source(found)
                args.append((field, str(self.map(nested).call())))
                values.append((field, UNKNOWN))
                continue
            if kind == "array":
                var = str(target.field().singular())
                parts = []
                for element_field, element_type in target.element():
                    if reads_aggregate:
                        cast = "int" if element_type == "int" else "str"
                        parts.append(f"{element_field}={cast}({var}.{element_field})")
                    elif package == "domain" and element_type not in PRIMITIVE_TYPES:
                        parts.append(f"{element_field}=domain.{element_type}({var}.{element_field})")
                    else:
                        parts.append(f"{element_field}={var}.{element_field}")
                args.append((field, f"tuple({package}.{target.record()}({', '.join(parts)}) for {var} in {read})"))
                items = json.loads(held) if held != UNKNOWN else None
                wanted = [element_field for element_field, _ in target.element()]
                if isinstance(items, list) and all(isinstance(item, dict) and set(wanted) <= set(item) for item in items):
                    values.append((field, json.dumps([{key: item[key] for key in wanted} for item in items])))
                else:
                    values.append((field, UNKNOWN))
                continue
            if reads_aggregate:
                args.append((field, f"int({read})" if str(target.type_text()) == "int" else f"str({read})"))
            elif package == "domain" and kind == "enum":
                args.append((field, f"domain.{target.type_text()}({read})"))
            else:
                args.append((field, read))
            values.append((field, held))
        params: list[tuple[str, str]] = []
        for source in sources.held():
            param = (str(source.expr()), str(source.type_ref()))
            if source in used and param not in params:
                params.append(param)
        mapper_def = MapperDef(MapperDefSpec(name=name, target=str(ask.target_ref()), params=tuple(params), args=tuple(args)))
        if any(existing.name() == mapper_def.name() and existing != mapper_def for existing in self._defs) and str(ask.occasion()):
            name = f"{name}For{ask.occasion()}"
            mapper_def = MapperDef(MapperDefSpec(name=name, target=str(ask.target_ref()), params=tuple(params), args=tuple(args)))
        for existing in self._defs:
            if existing.name() == mapper_def.name() and existing != mapper_def:
                raise ValueError(f"two mappers in {self._module} would be named {name}")
        if mapper_def not in self._defs:
            self._defs.append(mapper_def)
        return Mapped(MappedSpec(call=f"{name}({', '.join(param for param, _ in params)})", values=tuple(values)))


class Sample(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)

    def literal(self, target: Target) -> Text:
        value = json.loads(self._value)
        package = str(target.package())
        if str(target.kind()) == "array":
            items = []
            for item in value:
                parts = []
                for element_field, element_type in target.element():
                    if package == "domain" and element_type not in PRIMITIVE_TYPES:
                        parts.append(f"{element_field}=domain.{element_type}.{str(item[element_field]).upper()}")
                    else:
                        parts.append(f"{element_field}={json.dumps(item[element_field])}")
                items.append(f"{package}.{target.record()}({', '.join(parts)})")
            return Text(f"({', '.join(items)},)" if items else "()")
        if package == "domain" and str(target.kind()) == "enum":
            return Text(f"domain.{target.type_text()}.{str(value).upper()}")
        return Text(json.dumps(value))


class SamplesSpec(ts.Spec):

    def __init__(self, values: str, index: int, types: TypesSpec) -> None:
        self.values = values
        self.index = index
        self.types = types


class Samples(ts.ValueObject):

    _values: Text
    _index: Word
    _types: Types

    def __init__(self, spec: SamplesSpec) -> None:
        object.__setattr__(self, "_values", Text(spec.values))
        object.__setattr__(self, "_index", Word(str(spec.index)))
        object.__setattr__(self, "_types", Types(spec.types))

    def value(self, target: Target) -> Sample:
        values = json.loads(str(self._values))
        index = int(str(self._index))
        field = str(target.field())
        if field in values:
            listed = values[field]
            return Sample(json.dumps(listed[index % len(listed)]))
        array = str(target.kind()) == "array"
        wanted = list(target.element()) if array else [(field, str(target.type_text()))]
        found: dict[str, object] = {}
        for wanted_field, wanted_type in wanted:
            if wanted_field in values:
                listed = values[wanted_field]
                found[wanted_field] = listed[index % len(listed)]
                continue
            if str(self._types.kind(wanted_type)) == "enum":
                members = [member for member, _ in self._types.members(wanted_type)]
                found[wanted_field] = members[index % len(members)]
                continue
            nested = [
                element[wanted_field]
                for listed in values.values()
                if isinstance(listed, list)
                for item in listed
                if isinstance(item, list)
                for element in item
                if isinstance(element, dict) and wanted_field in element
            ]
            if not nested:
                raise ValueError(f"generator.toml gives no sample value for {wanted_field}, and no sample holds one")
            found[wanted_field] = nested[index % len(nested)]
        return Sample(json.dumps([found] if array else found[field]))


class FieldAskSpec(ts.Spec):

    def __init__(self, module: str, field: str, type_text: str, prefix: str) -> None:
        self.module = module
        self.field = field
        self.type_text = type_text
        self.prefix = prefix


class FieldAsk(ts.ValueObject):

    _module: Word
    _field: Word
    _type_text: Word
    _prefix: Word

    def __init__(self, spec: FieldAskSpec) -> None:
        object.__setattr__(self, "_module", Word(spec.module))
        object.__setattr__(self, "_field", Word(spec.field))
        object.__setattr__(self, "_type_text", Word(spec.type_text))
        object.__setattr__(self, "_prefix", Word(spec.prefix))

    def module(self) -> Word:
        return self._module

    def field(self) -> Word:
        return self._field

    def type_text(self) -> Word:
        return self._type_text

    def prefix(self) -> Word:
        return self._prefix


class RecordSpec(ts.Spec):

    def __init__(self, module: str, name: str, base: str, snapshot: bool) -> None:
        self.module = module
        self.name = name
        self.base = base
        self.snapshot = snapshot


class Record(ts.Entity):

    def __init__(self, spec: RecordSpec) -> None:
        self._module = spec.module
        self._name = spec.name
        self._base = spec.base
        self._snapshot = spec.snapshot
        self._targets: list[Target] = []

    @property
    def identity(self) -> str:
        return self._name

    def add(self, target: Target) -> None:
        self._targets.append(target)

    def name(self) -> Word:
        return Word(self._name)

    def module(self) -> Word:
        return Word(self._module)

    def base(self) -> Word:
        return Word(self._base)

    def snapshots(self) -> tuple[Word, ...]:
        return (Word(self._name + "Snapshot"),) if self._snapshot else ()

    def targets(self) -> tuple[Target, ...]:
        return tuple(self._targets)


class RecordsSpec(ts.Spec):

    def __init__(self, package: str, types: TypesSpec) -> None:
        self.package = package
        self.types = types


class Records(ts.Entity):

    def __init__(self, spec: RecordsSpec) -> None:
        self._package = spec.package
        self._types = Types(spec.types)
        self._owners: dict[str, tuple[str, str]] = {}
        self._declared: dict[str, list[Record]] = {}

    @property
    def identity(self) -> str:
        return self._package

    def declare(self, record: Record) -> None:
        self._declared.setdefault(str(record.module()), []).append(record)

    def declared(self, word: Word) -> tuple[Record, ...]:
        return tuple(self._declared.get(str(word), []))

    def modules(self) -> tuple[Word, ...]:
        return tuple(Word(module) for module in self._declared)

    def target(self, field_ask: FieldAsk) -> Target:
        module = str(field_ask.module())
        field = str(field_ask.field())
        type_text = str(field_ask.type_text())
        prefix = str(field_ask.prefix())
        kind = str(self._types.kind(type_text))
        if kind in ("scalar", "enum"):
            return Target(TargetSpec(field=field, type_text=type_text, kind=kind, package=self._package, record="",
                                     element=(), members=()))
        if kind == "shape":
            raise ValueError(f"{field} is a single {type_text}; a message carries a shape only as a list ({type_text}[])")
        shape = str(self._types.element(type_text))
        wanted = [shape] if kind == "array" else [
            str(self._types.element(member_type))
            for _, member_type in self._types.fields(shape)
            if str(self._types.kind(member_type)) == "array"
        ] + [shape]
        names: dict[str, str] = {}
        for claimed in wanted:
            owner = self._owners.get(claimed)
            if owner is not None and owner[0] == module:
                names[claimed] = owner[1]
                continue
            name = claimed if owner is None else prefix + claimed
            names[claimed] = name
            if any(str(record.name()) == name for record in self._declared.get(module, [])):
                continue
            record = Record(RecordSpec(module=module, name=name, base="Response", snapshot=False))
            for member_field, member_type in self._types.fields(claimed):
                if str(self._types.kind(member_type)) == "array" and claimed != shape:
                    raise ValueError(f"{claimed} holds a list inside a list, which a message does not carry")
                record.add(self.target(FieldAsk(FieldAskSpec(module=module, field=member_field, type_text=member_type, prefix=prefix))))
            self._declared.setdefault(module, []).append(record)
            if owner is None:
                self._owners[claimed] = (module, name)
        if kind == "array":
            return Target(TargetSpec(field=field, type_text=type_text, kind=kind, package=self._package,
                                     record=names[shape], element=tuple(self._types.fields(shape)), members=()))
        members = tuple(
            TargetSpec(
                field=member_field, type_text=member_type, kind=str(self._types.kind(member_type)),
                package=self._package,
                record=names.get(str(self._types.element(member_type)), "")
                if str(self._types.kind(member_type)) == "array" else "",
                element=tuple(self._types.fields(str(self._types.element(member_type))))
                if str(self._types.kind(member_type)) == "array" else (),
                members=(),
            )
            for member_field, member_type in self._types.fields(shape)
        )
        return Target(TargetSpec(field=field, type_text=type_text, kind=kind, package=self._package,
                                 record=names[shape], element=(), members=members))


class ReadoutSpec(ts.Spec):

    def __init__(self, reads: tuple[tuple[str, str], ...], aggregate: str, types: TypesSpec) -> None:
        self.reads = reads
        self.aggregate = aggregate
        self.types = types


class Readout(ts.ValueObject):

    _reads: Pairs
    _aggregate: Word
    _types: Types

    def __init__(self, spec: ReadoutSpec) -> None:
        object.__setattr__(self, "_reads", Pairs(spec.reads))
        object.__setattr__(self, "_aggregate", Word(spec.aggregate))
        object.__setattr__(self, "_types", Types(spec.types))

    def of(self, pairs: Pairs) -> Pairs:
        read_values: list[tuple[str, str]] = []
        for read, read_type in self._reads:
            kind = str(self._types.kind(read_type))
            held = pairs.get(read)
            if kind == "enum" or held is None or str(held) == UNKNOWN:
                read_values.append((read, UNKNOWN))
                continue
            if kind != "array":
                read_values.append((read, str(held)))
                continue
            wanted = [field for field, _ in self._types.fields(str(self._types.element(read_type)))]
            items = json.loads(str(held))
            if all(set(wanted) <= set(item) for item in items):
                read_values.append((read, json.dumps([{key: item[key] for key in wanted} for item in items])))
            else:
                read_values.append((read, UNKNOWN))
        read_values.append((str(self._aggregate), UNKNOWN))
        return Pairs(tuple(read_values))


class EchoSpec(ts.Spec):

    def __init__(self, samples: SamplesSpec) -> None:
        self.samples = samples


class Echo(ts.ValueObject):

    _samples: Samples

    def __init__(self, spec: EchoSpec) -> None:
        object.__setattr__(self, "_samples", Samples(spec.samples))

    def of(self, ask: Ask) -> Mapped:
        args: list[tuple[str, str]] = []
        values: list[tuple[str, str]] = []
        for target in ask.targets():
            field = str(target.field())
            found = ask.sources().find(target.field())
            if found is not None and str(target.kind()) != "array":
                args.append((field, str(found.prefix()) + field))
                values.append((field, str(found.holds().get(field))))
                continue
            sample = self._samples.value(target)
            args.append((field, str(sample.literal(target))))
            values.append((field, str(sample)))
        return Mapped(MappedSpec(call=", ".join(f"{field}={expr}" for field, expr in args), values=tuple(values)))


class ModelSpec(ts.Spec):

    def __init__(self, language: str, story: str, infra: str, composition: str, implementations: str, generator: str) -> None:
        self.language = language
        self.story = story
        self.infra = infra
        self.composition = composition
        self.implementations = implementations
        self.generator = generator


class Model(ts.Entity):

    def __init__(self, spec: ModelSpec) -> None:
        self._story = tomllib.loads(spec.story)
        self._infra = tomllib.loads(spec.infra)
        self._composition = tomllib.loads(spec.composition)
        self._implementations = tomllib.loads(spec.implementations)
        moved = [f"implementations.toml declares {shown}, which moved to infra.toml: implementations.toml holds only "
                 f"[implementations] and [environments]" for key, shown in MOVED_TO_INFRA if key in self._implementations]
        if moved:
            raise ValueError(*moved)
        self._generator = tomllib.loads(spec.generator)
        language = tomllib.loads(spec.language)
        composition = self._composition
        aggregate_table = composition["aggregate"]
        self._context = str(composition["context"])
        self._app = str(self._infra["app"])
        self._Aggregate = str(aggregate_table["name"])
        self._aggregate = str(Word(self._Aggregate).snake())
        self._identity = str(aggregate_table["identity"])
        self._Orchestrator = self._Aggregate + "Orchestrator"
        self._engine_declared = bool(self._infra.get("engine", {}))
        self._spec_fields = [(str(field), str(type_text)) for field, type_text in aggregate_table["spec"].items()]
        self._reads = [(str(field), str(type_text)) for field, type_text in aggregate_table["reads"].items()]
        self._read_types = dict(self._reads)
        self._commands = dict(aggregate_table.get("commands", {}))
        self._enums = {str(name): [str(member) for member in members] for name, members in composition.get("enums", {}).items()}
        shapes = dict(composition.get("shapes", {}))
        shapes.update(composition.get("messages", {}))
        self._shapes = {str(name): [(str(field), str(type_text)) for field, type_text in fields.items()] for name, fields in shapes.items()}
        self._types_args = (
            tuple((name, tuple(members)) for name, members in self._enums.items()),
            tuple((name, tuple(fields)) for name, fields in self._shapes.items()),
            self._Aggregate,
            tuple(self._spec_fields),
        )
        self._types = Types(TypesSpec(*self._types_args))
        for sampled_field, sampled in dict(self._generator.get("sample_values", {})).items():
            if isinstance(sampled, list) and not sampled:
                raise ValueError(f"generator.toml lists no sample values for {sampled_field}")
        self._sample_values = json.dumps(self._generator.get("sample_values", {}))
        self._samples = Samples(SamplesSpec(values=self._sample_values, index=0, types=TypesSpec(*self._types_args)))
        self._registry: dict[str, str] = dict(self._spec_fields)
        for command in self._commands.values():
            for field, type_text in command.get("takes", {}).items():
                self._registry.setdefault(str(field), str(type_text))
        self._inline: dict[tuple[str, str, str], str] = {}
        for port_name, port in composition.get("ports", {}).items():
            for operation_name, operation in port.get("operations", {}).items():
                for side in ("request", "response"):
                    for listed in operation.get(side, []):
                        if ":" in listed:
                            field, type_text = (part.strip() for part in str(listed).split(":", 1))
                            record_name = str(Word(str(operation_name)).pascal()) + side.capitalize()
                            self._inline[(str(Word(str(port_name)).snake()), record_name, field)] = type_text
        for operation_name, operation in composition.get("client", {}).get("operations", {}).items():
            for side in ("request", "response"):
                record_name = str(Word(str(operation_name)).pascal()) + side.capitalize()
                for listed in operation.get(side, []):
                    if ":" in listed:
                        field, type_text = (part.strip() for part in str(listed).split(":", 1))
                        self._inline[("client", record_name, field)] = type_text
                for step in operation.get("steps", []):
                    stepped = str(step).split(".", 1)[-1]
                    for port_name, port in composition.get("ports", {}).items():
                        for port_side in ("request", "response"):
                            for listed in port.get("operations", {}).get(stepped, {}).get(port_side, []):
                                if ":" in listed:
                                    field, type_text = (part.strip() for part in str(listed).split(":", 1))
                                    self._inline.setdefault(("stepped", record_name, field), type_text)
        self._registry[self._aggregate] = self._Aggregate
        self._packages = {
            package: Records(RecordsSpec(package=package, types=TypesSpec(*self._types_args)))
            for package in ("client", "ports", "relays")
        }
        self._domain_targets: dict[str, list[Target]] = {}
        takes = [(self._Aggregate + "Spec", self._spec_fields)] + [
            (str(Word(str(command)).pascal()) + "Spec", [(str(f), str(t)) for f, t in table.get("takes", {}).items()])
            for command, table in self._commands.items()
        ]
        for spec_name, fields in takes:
            targets = []
            for field, type_text in fields:
                kind = str(self._types.kind(type_text))
                if kind == "array":
                    element = str(self._types.element(type_text))
                    record = element if element.endswith("Spec") else element + "Spec"
                    targets.append(Target(TargetSpec(field=field, type_text=type_text, kind=kind, package="domain",
                                                     record=record, element=tuple(self._types.fields(element)), members=())))
                elif kind in ("scalar", "enum"):
                    targets.append(Target(TargetSpec(field=field, type_text=type_text, kind=kind, package="domain",
                                                     record="", element=(), members=())))
                else:
                    raise ValueError(f"{spec_name} takes {field} as a {type_text}, which a spec carries only as a list")
            self._domain_targets[spec_name] = targets
        self._echo = {
            index: Echo(EchoSpec(SamplesSpec(values=self._sample_values, index=index, types=TypesSpec(*self._types_args))))
            for index in (0, 1)
        }
        self._readout = Readout(ReadoutSpec(reads=tuple(self._reads), aggregate=self._aggregate, types=TypesSpec(*self._types_args)))
        named: list[tuple[str, str, str]] = [
            ("snake", "context", self._context), ("snake", "app", self._app),
            ("pascal", "[aggregate] name", self._Aggregate), ("snake", "[aggregate] identity", self._identity),
        ]
        if self._context in RESERVED:
            raise ValueError(f"context names {self._context!r}, a name the rendered tree already uses for its own package")
        named.extend(("snake", "[aggregate.spec]", field) for field, _ in self._spec_fields)
        named.extend(("snake", "[aggregate.reads]", field) for field, _ in self._reads)
        for command, table in self._commands.items():
            named.append(("operation", "[aggregate.commands]", str(command)))
            named.extend(("snake", f"{command} takes", str(field)) for field in table.get("takes", {}))
            named.extend(("snake", f"{command} outcomes", str(outcome)) for outcome in table.get("outcomes", []))
        for name, fields in self._shapes.items():
            named.append(("pascal", "[shapes] or [messages]", name))
            named.extend(("snake", name, field) for field, _ in fields)
        for name, members in self._enums.items():
            named.append(("pascal", "[enums]", name))
            named.extend(("snake", name, member) for member in members)
        for section in ("client", "orchestrator"):
            for operation_name, operation in composition.get(section, {}).get("operations", {}).items():
                named.append(("operation", f"[{section}.operations]", str(operation_name)))
                named.extend(("snake", str(operation_name), str(field).split(":", 1)[0].strip())
                             for field in list(operation.get("request", [])) + list(operation.get("response", [])))
        for key, table in composition.get("actions", {}).items():
            named.append(("snake", "[actions]", str(key)))
            named.append(("pascal", f"actions.{key} port", str(table.get("port", ""))))
            for operation_name, operation in table.get("operations", {}).items():
                named.append(("operation", f"[actions.{key}.operations]", str(operation_name)))
                named.extend(("snake", str(operation_name), str(field))
                             for field in list(operation.get("request", [])) + list(operation.get("response", [])))
                named.extend(("snake", f"{operation_name} calls_on", str(outcome)) for outcome in operation.get("calls_on", []))
        for signal_name, signal in composition.get("signals", {}).items():
            named.append(("operation", "[signals]", str(signal_name)))
            named.extend(("snake", str(signal_name), str(field)) for field in signal.get("payload", []))
        for port_name, port in composition.get("ports", {}).items():
            named.append(("pascal", "[ports]", str(port_name)))
            for operation_name, operation in port.get("operations", {}).items():
                named.append(("operation", f"[ports.{port_name}]", str(operation_name)))
                named.extend(("snake", str(operation_name), str(listed).split(":", 1)[0].strip())
                             for listed in list(operation.get("request", [])) + list(operation.get("response", [])))
        for port_name, choices in self._implementations.get("implementations", {}).items():
            for key, implementation in choices.items():
                if implementation.get("body") == "agent":
                    named.append(("pascal", f"[implementations.{port_name}.{key}] class", str(implementation.get("class", ""))))
        engine = self._infra.get("engine", {}).get("restate", {})
        named.extend(("variable", f"[engine.restate] {key}", str(engine[key]))
                     for key in ("engine_url_variable",) if key in engine)
        if "engine_path" in engine:
            named.append(("path", "[engine.restate] engine_path", str(engine["engine_path"])))
        for storage_name, storage in self._infra.get("storage", {}).items():
            named.append(("snake", "[storage]", str(storage_name)))
            if "location_variable" in storage:
                named.append(("variable", f"[storage.{storage_name}] location_variable", str(storage["location_variable"])))
        host = self._infra.get("hosts", {}).get("http", {})
        if "listen_port_variable" in host:
            named.append(("variable", "[hosts.http] listen_port_variable", str(host["listen_port_variable"])))
        for pattern_name, where, name in named:
            pattern, description = PATTERNS[pattern_name]
            if pattern.fullmatch(name) is None or keyword.iskeyword(name):
                raise ValueError(f"{where} names {name!r}, which is not a {description}")
        domain_nouns = {str(code_name) for term in language.get("terms", []) for code_name in term.get("code_names", [])}
        for term in language.get("terms", []):
            for spelling in (term.get("term"), term.get("short")):
                if spelling:
                    domain_nouns.add(str(Word(re.sub(r"[^A-Za-z0-9]+", "_", str(spelling)).strip("_").lower()).pascal()))
        for key, table in composition.get("actions", {}).items():
            if str(Word(str(key)).pascal()) not in domain_nouns:
                raise ValueError(f"[actions.{key}] is named for {str(Word(str(key)).pascal())!r}, which is neither a term nor a "
                                 f"code name in language.toml; a class of actions is named for the domain term it acts on "
                                 f"(a term's name or its short form), never for its port ({table.get('port', '')})")
            for operation_name, operation in table.get("operations", {}).items():
                if "builds" in operation and str(operation["builds"]) != self._Aggregate:
                    raise ValueError(f"actions.{key}.operations.{operation_name} builds {str(operation['builds'])!r}, and the "
                                     f"one aggregate it can build is {self._Aggregate!r}")
        self._messages: dict[tuple[str, str], Record] = {}
        self._port_of: dict[str, str] = {}
        self._port_ops: dict[str, list[str]] = {}
        self._stores: dict[str, str] = {}
        self._relay_ops: dict[str, list[tuple[str, str, str, str, str]]] = {}
        self._orchestrator_modes: dict[str, list[str]] = {}
        self._binding: dict[str, object] = {
            "context": self._context, "Context": str(Word(self._context).pascal()), "app": self._app,
            "App": str(Word(self._app).pascal()), "Aggregate": self._Aggregate, "aggregate": self._aggregate,
            "aggregates": str(Word(self._aggregate).plural()), "identity": self._identity,
            "ClientClass": str(Word(self._context).pascal()) + "Client", "Service": self._Aggregate + "Service",
            "Rejected": self._Aggregate + "Rejected", "rejected": self._aggregate + "_rejected",
        }
        self._frames: dict[tuple[str, str], dict[str, object]] = {}

    @property
    def identity(self) -> str:
        return self._context

    def messages(self) -> None:
        composition = self._composition
        declared: list[tuple[str, str, str, str, list[str], bool, str, bool]] = []
        for port_name, port in composition.get("ports", {}).items():
            module = str(Word(port_name).snake())
            self._port_ops[port_name] = []
            for operation_name, operation in port.get("operations", {}).items():
                request = [str(listed).split(":", 1)[0].strip() for listed in operation.get("request", [])]
                response = [str(listed).split(":", 1)[0].strip() for listed in operation.get("response", [])]
                if self._aggregate in request + response:
                    self._stores[port_name] = port_name.replace("Repository", "Store")
                Operation = str(Word(operation_name).pascal())
                declared.append(("ports", module, Operation + "Request", "Request", request, False, port_name, False))
                declared.append(("ports", module, Operation + "Response", "Response", response, False, port_name, False))
                if operation_name in self._port_of:
                    raise ValueError(f"ports {self._port_of[operation_name]} and {port_name} both declare {operation_name}, and "
                                     f"ports exports one {Operation}Request and one {Operation}Response, so one port declares it")
                self._port_of[operation_name] = port_name
                self._port_ops[port_name].append(operation_name)
        client_steps = [str(step) for operation in composition.get("client", {}).get("operations", {}).values()
                        for step in operation.get("steps", [])]
        if not self._engine_declared:
            unrun = [f"composition.toml declares [{section}], which runs on a durable-execution engine, and infra.toml declares "
                     f"no [engine]: without one, a client operation's steps call its ports directly"
                     for section in ("orchestrator", "actions", "signals") if composition.get(section)]
            unrun.extend(f"step {step} runs the orchestrator, and infra.toml declares no [engine] to run it: without one, a "
                         f"client operation's steps call its ports directly"
                         for step in client_steps if step.split(".", 1)[0] == "orchestrator")
            if unrun:
                raise ValueError(*unrun)
        for step in client_steps:
            kind, rest = str(step).split(".", 1)
            if kind != "orchestrator":
                continue
            mode, operation_name = rest.split("_", 1)
            if mode not in ("start", "run"):
                raise ValueError(f"step {step} names the orchestrator without start_ or run_, the two ways a client step waits on it")
            modes = self._orchestrator_modes.setdefault(operation_name, [])
            if mode not in modes:
                modes.append(mode)
        orchestrator_operations = composition.get("orchestrator", {}).get("operations", {})
        if self._engine_declared:
            self._relay_ops[self._Orchestrator + "Relay"] = []
            if len(orchestrator_operations) != 1:
                raise ValueError("the composition declares one orchestrator operation, because a workflow keeps one main")
        relay_module = str(Word(self._Orchestrator).snake()) + "_relay"
        for operation_name, operation in orchestrator_operations.items():
            Operation = str(Word(operation_name).pascal())
            declared.append(("relays", relay_module, Operation + "Request", "Request", list(operation["request"]), True, self._Orchestrator, False))
            declared.append(("relays", relay_module, Operation + "Response", "Response", list(operation["response"]), True, self._Orchestrator, False))
            for mode in self._orchestrator_modes.get(operation_name, []):
                returns = Operation + "Response"
                if mode == "start":
                    returns = "Start" + Operation + "Response"
                    declared.append(("relays", relay_module, returns, "Response", [self._identity], False, self._Orchestrator, False))
                self._relay_ops[self._Orchestrator + "Relay"].append(
                    (f"{mode}_{operation_name}", operation_name + "_request", Operation + "Request", returns, operation_name))
        for key, table in composition.get("actions", {}).items():
            Actions = str(Word(str(key)).pascal()) + "Actions"
            module = str(Word(Actions).snake()) + "_relay"
            self._relay_ops[Actions + "Relay"] = []
            for operation_name, operation in table.get("operations", {}).items():
                Operation = str(Word(operation_name).pascal())
                declared.append(("relays", module, Operation + "Request", "Request", list(operation["request"]), True, Actions, False))
                declared.append(("relays", module, Operation + "Response", "Response", list(operation["response"]), True, Actions, False))
                self._relay_ops[Actions + "Relay"].append(
                    (f"run_{operation_name}", operation_name + "_request", Operation + "Request", Operation + "Response", operation_name))
        signals = composition.get("signals", {})
        if signals:
            module = str(Word(self._Orchestrator).snake()) + "_signal_relay"
            self._relay_ops[self._Orchestrator + "SignalRelay"] = []
            for signal_name, signal in signals.items():
                if signal.get("resolved", False):
                    raise ValueError(f"signals.{signal_name} is resolved, and this renderer renders only the wait")
                Signal = str(Word(str(signal_name)).pascal())
                declared.append(("relays", module, f"Await{Signal}Request", "Request", [self._identity], False, self._Orchestrator + "Signal", False))
                declared.append(("relays", module, f"Await{Signal}Response", "Response", list(signal.get("payload", [])), True, self._Orchestrator + "Signal", False))
                self._relay_ops[self._Orchestrator + "SignalRelay"].append(
                    (f"await_{signal_name}", f"await_{signal_name}_request", f"Await{Signal}Request", f"Await{Signal}Response", str(signal_name)))
        for operation_name, operation in composition.get("client", {}).get("operations", {}).items():
            Operation = str(Word(operation_name).pascal())
            declared.append(("client", "client", Operation + "Request", "Request",
                             [str(listed).split(":", 1)[0].strip() for listed in operation["request"]], False, "", False))
            declared.append(("client", "client", Operation + "Response", "Response",
                             [str(listed).split(":", 1)[0].strip() for listed in operation["response"]], False, "", True))
        for package, module, name, base, fields, snapshot, prefix, reading in declared:
            records = self._packages[package]
            record = Record(RecordSpec(module=module, name=name, base=base, snapshot=snapshot))
            for field in fields:
                if package in ("ports", "client") and (module, name, field) in self._inline:
                    type_text = self._inline[(module, name, field)]
                elif reading and field in self._read_types:
                    type_text = self._read_types[field]
                elif field in self._registry:
                    type_text = self._registry[field]
                elif field in self._read_types:
                    type_text = self._read_types[field]
                elif package == "client" and ("stepped", name, field) in self._inline:
                    type_text = self._inline[("stepped", name, field)]
                else:
                    raise ValueError(f"{field} has no type: no aggregate spec, read, command, or annotation names it; write it "
                                     f"as \"{field}: <type>\" in the list that names it")
                record.add(records.target(FieldAsk(FieldAskSpec(module=module, field=field, type_text=type_text, prefix=prefix))))
            records.declare(record)
            self._messages[(package, name)] = record
        for package in ("client", "ports", "relays"):
            records = self._packages[package]
            for module_word in records.modules():
                for record in records.declared(module_word):
                    field_frames: list[dict[str, object]] = []
                    for target in record.targets():
                        kind = str(target.kind())
                        element = list(target.element())
                        field_frames.append({
                            "field": str(target.field()),
                            "dto_type": {"scalar": str(target.type_text()), "enum": "str",
                                         "array": f"tuple[{target.record()}, ...]"}.get(kind, str(target.record())),
                            "scalar": [{}] if kind in ("scalar", "enum") else [],
                            "array": [{}] if kind == "array" else [],
                            "var": str(target.field().singular()),
                            "primitive": "int" if str(target.type_text()) == "int" else "str",
                            "element_record": str(target.record()),
                            "element": [
                                {"name": name, "primitive": "int" if type_text == "int" else "str",
                                 "sep": ", " if index < len(element) - 1 else ""}
                                for index, (name, type_text) in enumerate(element)
                            ],
                        })
                    names = [str(target.field()) for target in record.targets()]
                    note_name = str(record.name().snake().spaced())
                    article = "an" if note_name[:1] in "aeiou" else "a"
                    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + ", and " + (names[-1] if names else "")
                    frame: dict[str, object] = {
                        "Record": str(record.name()), "record": str(record.name().snake()), "base": str(record.base()),
                        "fields": field_frames, "snapshot": [{}] if record.snapshots() else [],
                        "shape_note": f"{article} {note_name} is its {listed}" if names else f"{article} {note_name} is empty",
                        "module": str(module_word),
                    }
                    if record.snapshots():
                        values = {str(target.field()): json.loads(str(self._samples.value(target))) for target in record.targets()}
                        frame["sample"] = ", ".join(f"{target.field()}={self._samples.value(target).literal(target)}" for target in record.targets())
                        frame["sample_bytes"] = repr(json.dumps(values).encode())
                        wrong = ['b"[]"']
                        if names:
                            first = record.targets()[0]
                            broken = dict(values)
                            broken[names[0]] = "one" if str(first.type_text()) == "int" else 1
                            wrong = ['b"{}"'] + wrong + [repr(json.dumps(broken).encode())]
                        frame["wrong_shapes"] = ", ".join(wrong)
                    self._frames[(package, str(record.name()))] = frame
        for port_name, store in self._stores.items():
            operations = [(op, self._messages[("ports", str(Word(op).pascal()) + "Request")],
                           self._messages[("ports", str(Word(op).pascal()) + "Response")]) for op in self._port_ops[port_name]]
            saves = [(op, request) for op, request, _ in operations if any(str(t.kind()) == "aggregate" for t in request.targets())]
            loads = [(op, request, response) for op, request, response in operations
                     if any(str(t.kind()) == "aggregate" for t in response.targets())]
            if len(operations) != 2 or len(saves) != 1 or len(loads) != 1 or \
                    [str(t.field()) for t in loads[0][1].targets()] != [self._identity] or \
                    self._messages[("ports", str(Word(saves[0][0]).pascal()) + "Response")].targets():
                raise ValueError(f"{port_name} carries {self._aggregate}, so it is a store: one save of it that answers nothing and one load of it by {self._identity}")
            carried = next(t for t in saves[0][1].targets() if str(t.kind()) == "aggregate")
            self._frames[("store", port_name)] = {
                "Port": port_name, "Store": store, "store_attr": str(Word(store).snake()),
                "aggregates": str(Word(self._aggregate).plural()), "Record": str(carried.record()),
                "save": saves[0][0], "Save": str(Word(saves[0][0]).pascal()),
                "load": loads[0][0], "Load": str(Word(loads[0][0]).pascal()),
                "record_sample": ", ".join(f"{m.field()}={self._samples.value(m).literal(m)}" for m in carried.members()),
                "identity_sample": str(self._samples.value(next(m for m in carried.members() if str(m.field()) == self._identity))),
            }

    def bodies(self) -> None:
        composition = self._composition
        Aggregate = self._Aggregate
        aggregate = self._aggregate
        identity = self._identity
        Orchestrator = self._Orchestrator
        aggregates = str(Word(aggregate).plural())
        blank: dict[str, object] = {"build": [], "port_call": [], "store_call": [], "assign": "", "holder": "",
                                    "call": "", "argument": "", "repository": ""}
        fakes: dict[tuple[str, str], Mapped] = {}
        for (package, name), record in self._messages.items():
            if package not in ("ports", "relays") or not name.endswith("Request"):
                continue
            operation = name.removesuffix("Request")
            for returned_name in (operation + "Response", "Start" + operation + "Response"):
                returned = self._messages.get((package, returned_name))
                if returned is None or any(str(t.kind()) == "aggregate" for t in returned.targets()):
                    continue
                param = str(Word(operation).snake()) + "_request"
                for index in (0, 1):
                    ask = Ask(AskSpec(name=returned_name, target_ref=returned_name, allow_empty=False))
                    for target in returned.targets():
                        ask.target(target)
                    ask.source(Source(SourceSpec(expr=param, type_ref=name, kind="plain", prefix=param + ".",
                                                 holds=tuple((str(t.field()), UNKNOWN) for t in record.targets()
                                                             if str(t.kind()) != "array"))))
                    fakes[(package, returned_name + str(index))] = self._echo[index].of(ask)
        self._fakes = fakes

        def_frames: list[dict[str, object]] = []
        mappers = Mappers(MappersSpec(module="service"))
        dependencies: list[dict[str, object]] = []
        service_ops: list[dict[str, object]] = []
        service_tests: list[dict[str, object]] = []
        for operation_name, operation in composition.get("client", {}).get("operations", {}).items():
            Operation = str(Word(operation_name).pascal())
            occasion = Operation
            request_record = self._messages[("client", Operation + "Request")]
            response_record = self._messages[("client", Operation + "Response")]
            sources = Sources(SourcesSpec(name=operation_name))
            sources.hold(Source(SourceSpec(
                expr=operation_name + "_request", type_ref=f"client.{Operation}Request", kind="plain",
                prefix=operation_name + "_request.",
                holds=tuple((str(t.field()), str(self._samples.value(t))) for t in request_record.targets()))))
            statements: list[dict[str, object]] = []
            checks: list[dict[str, object]] = []
            seeds: list[dict[str, object]] = []
            built = False
            saved = False
            test_name = f"{operation_name}_answers_from_its_steps"
            for step in operation.get("steps", []):
                kind, rest = str(step).split(".", 1)
                if kind in ("identity", "repository", "gateway"):
                    if rest not in self._port_of:
                        raise ValueError(f"step {step} names {rest}, which no port declares")
                    port_name = self._port_of[rest]
                    Step = str(Word(rest).pascal())
                    port_request = self._messages[("ports", Step + "Request")]
                    port_response = self._messages[("ports", Step + "Response")]
                    carries = any(str(t.kind()) == "aggregate" for t in port_request.targets())
                    if carries and not built:
                        ask = Ask(AskSpec(name=f"MapTo{Aggregate}Spec", target_ref=f"domain.{Aggregate}Spec", allow_empty=True, occasion=occasion))
                        for target in self._domain_targets[Aggregate + "Spec"]:
                            ask.target(target)
                        for held in sources.held():
                            ask.source(held)
                        mapped = mappers.map(ask)
                        statements.append(dict(blank, build=[{}], argument=str(mapped.call())))
                        sources.hold(Source(SourceSpec(expr=aggregate, type_ref=f"domain.{Aggregate}", kind="aggregate",
                                                       prefix=aggregate + ".", holds=tuple(self._readout.of(mapped.values())))))
                        built = True
                    if port_request.targets():
                        ask = Ask(AskSpec(name=f"MapTo{Step}Request", target_ref=f"ports.{Step}Request", allow_empty=False, occasion=occasion))
                        for target in port_request.targets():
                            ask.target(target)
                        for held in sources.held():
                            ask.source(held)
                        port_mapped = mappers.map(ask)
                        argument = str(port_mapped.call())
                    else:
                        port_mapped = Mapped(MappedSpec(call="", values=()))
                        argument = f"ports.{Step}Request()"
                    local = rest + "_response"
                    assign = f"{local} = " if port_response.targets() else ""
                    if port_name in self._stores:
                        holder = str(Word(self._stores[port_name]).snake())
                        dependency: dict[str, object] = {"dependency": holder, "dependency_type": f"ports.{self._stores[port_name]}"}
                        statements.append(dict(blank, store_call=[{}], holder=holder, repository=str(Word(port_name).snake()),
                                               assign=assign, call=rest, argument=argument))
                    else:
                        holder = str(Word(port_name).snake())
                        dependency = {"dependency": holder, "dependency_type": f"ports.{port_name}"}
                        statements.append(dict(blank, port_call=[{}], holder=holder, assign=assign, call=rest, argument=argument))
                        pairs = port_mapped.values()
                        if port_request.targets() and all(str(value) != UNKNOWN for _, value in pairs):
                            reads = ", ".join(f"received.{t.field()}" for t in port_request.targets())
                            expected = ", ".join(str(Sample(str(pairs.get(str(t.field())))).literal(t)) for t in port_request.targets())
                            checks.append({"check": f"[({reads},) for received in fake_{holder}.{rest}_requests] == [({expected},)]"})
                    if dependency not in dependencies:
                        dependencies.append(dependency)
                    saved = saved or carries
                    loaded = [t for t in port_response.targets() if str(t.kind()) == "aggregate"]
                    if loaded:
                        members = loaded[0].members()
                        member_values = tuple((str(m.field()), str(self._samples.value(m))) for m in members)
                        source = Source(SourceSpec(expr=local, type_ref=f"ports.{Step}Response", kind="plain",
                                                          prefix=f"{local}.{loaded[0].field()}.", holds=member_values))
                        ask = Ask(AskSpec(name=f"MapTo{Aggregate}SpecWhenLoaded", target_ref=f"domain.{Aggregate}Spec", allow_empty=False, occasion=occasion))
                        for target in self._domain_targets[Aggregate + "Spec"]:
                            ask.target(target)
                        ask.source(source)
                        for held in sources.held():
                            if str(held.kind()) != "aggregate":
                                ask.source(held)
                        mapped = mappers.map(ask)
                        statements.append(dict(blank, build=[{}], argument=str(mapped.call())))
                        sources.hold(source)
                        sources.hold(Source(SourceSpec(expr=aggregate, type_ref=f"domain.{Aggregate}", kind="aggregate",
                                                       prefix=aggregate + ".", holds=tuple(self._readout.of(mapped.values())))))
                        built = True
                        identity_value = str(Pairs(member_values).get(identity))
                        record_args = ", ".join(f"{m.field()}={self._samples.value(m).literal(m)}" for m in members)
                        seeds.append({"seed": f"fake_{Word(self._stores[port_name]).snake()}.{aggregates}[{identity_value}] = "
                                              f"ports.{loaded[0].record()}({record_args})"})
                        test_name = f"{operation_name}_answers_the_{aggregate}_it_loads"
                    elif port_response.targets():
                        sources.hold(Source(SourceSpec(expr=local, type_ref=f"ports.{Step}Response", kind="plain",
                                                       prefix=local + ".", holds=tuple(fakes[("ports", Step + "Response1")].values()))))
                elif kind == "orchestrator":
                    mode, orchestrator_operation = rest.split("_", 1)
                    Step = str(Word(orchestrator_operation).pascal())
                    relay_request = self._messages[("relays", Step + "Request")]
                    ask = Ask(AskSpec(name=f"MapTo{Step}Request", target_ref=f"relays.{Step}Request", allow_empty=False, occasion=occasion))
                    for target in relay_request.targets():
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    mapped = mappers.map(ask)
                    holder = str(Word(Orchestrator).snake()) + "_relay"
                    dependency = {"dependency": holder, "dependency_type": f"relays.{Orchestrator}Relay"}
                    if dependency not in dependencies:
                        dependencies.append(dependency)
                    returned_name = ("Start" if mode == "start" else "") + Step + "Response"
                    result = str(Word(returned_name).snake())
                    statements.append(dict(blank, port_call=[{}], holder=holder, assign=f"{result} = ",
                                           call=rest, argument=str(mapped.call())))
                    pairs = mapped.values()
                    if relay_request.targets() and all(str(value) != UNKNOWN for _, value in pairs):
                        reads = ", ".join(f"received.{t.field()}" for t in relay_request.targets())
                        expected = ", ".join(str(Sample(str(pairs.get(str(t.field())))).literal(t)) for t in relay_request.targets())
                        checks.append({"check": f"[({reads},) for received in fake_{holder}.received] == [({expected},)]"})
                    if saved:
                        checks.append({"check": f"fake_{holder}.saved_when_received == [True]"})
                    returned = self._messages[("relays", returned_name)]
                    echoed = Ask(AskSpec(name=returned_name, target_ref=returned_name, allow_empty=False, occasion=occasion))
                    for target in returned.targets():
                        echoed.target(target)
                    echoed.source(Source(SourceSpec(expr="sent", type_ref="sent", kind="plain", prefix="sent.", holds=tuple(pairs))))
                    sources.hold(Source(SourceSpec(expr=result, type_ref=f"relays.{returned_name}",
                                                   kind="plain", prefix=result + ".",
                                                   holds=tuple(self._echo[0].of(echoed).values()))))
                    test_name = f"{operation_name}_{rest}_with_the_{aggregate}_it_built"
                else:
                    raise ValueError(f"client step {step} is of a kind this renderer does not know: {kind}")
            ask = Ask(AskSpec(name=f"MapTo{Operation}Response", target_ref=f"client.{Operation}Response", allow_empty=False, occasion=occasion))
            for target in response_record.targets():
                ask.target(target)
            for held in sources.held():
                ask.source(held)
            answered = mappers.map(ask)
            for target in response_record.targets():
                value = str(answered.values().get(str(target.field())))
                local = f"{operation_name}_response.{target.field()}"
                if value == UNKNOWN and str(target.kind()) == "enum":
                    member_names = ", ".join(json.dumps(member) for member, _ in self._types.members(str(target.type_text())))
                    checks.append({"check": f"{local} in ({member_names})"})
                elif value != UNKNOWN:
                    checks.append({"check": f"{local} == {Sample(value).literal(target)}"})
            service_ops.append({"operation": operation_name, "Operation": Operation, "statements": statements,
                                "answer": str(answered.call())})
            service_tests.append({"name": test_name, "operation": operation_name, "Operation": Operation,
                                  "seeds": seeds, "checks": checks,
                                  "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request_record.targets())})
        for made in mappers.defs():
            def_frames.append({
                "Mapper": str(made.name()), "target": str(made.target()),
                "params": [{"param": param, "param_type": param_type} for param, param_type in made.params()],
                "args": [{"field": field, "expr": expr} for field, expr in made.args()],
            })
        self._binding["mappers"] = def_frames
        self._binding["dependencies"] = dependencies
        self._binding["service_operations"] = service_ops
        self._service_tests = service_tests
        aliases = {str(d["dependency_type"]).split(".", 1)[0] for d in dependencies} | {"client"}
        for made in mappers.defs():
            aliases.add(str(made.target()).split(".", 1)[0])
            aliases.update(param_type.split(".", 1)[0] for _, param_type in made.params())
        self._binding["service_imports"] = [
            {"module": module, "alias": alias}
            for module, alias in (("application.ports", "ports"), ("application.relays", "relays"),
                                  ("client", "client"), ("domain", "domain"))
            if alias in aliases
        ]
        self._binding["service_refuses"] = [{}] if any(
            statement["build"] for operation in service_ops for statement in typing.cast(list[dict[str, object]], operation["statements"])
        ) else []

    def actions(self) -> None:
        Aggregate = self._Aggregate
        aggregate = self._aggregate
        identity = self._identity
        aggregates = str(Word(aggregate).plural())
        blank: dict[str, object] = {"build": [], "port_call": [], "store_call": [], "assign": "", "holder": "",
                                    "call": "", "argument": "", "repository": ""}
        rendered: list[dict[str, object]] = []
        for key, table in self._composition.get("actions", {}).items():
            Key = str(Word(str(key)).pascal())
            Actions = Key + "Actions"
            port_name = str(table["port"])
            if port_name not in self._port_ops:
                raise ValueError(f"actions.{key} names port {port_name}, which [ports] does not declare")
            store = self._stores.get(port_name)
            holder = str(Word(store).snake()) if store else str(Word(port_name).snake())
            mappers = Mappers(MappersSpec(module=str(Word(Actions).snake())))
            operations: list[dict[str, object]] = []
            tests: list[dict[str, object]] = []
            commanded = False
            builds = False
            steps = [str(step) for orchestrated in self._composition.get("orchestrator", {}).get("operations", {}).values()
                     for step in orchestrated.get("steps", [])]
            for operation_name, operation in table.get("operations", {}).items():
                Operation = str(Word(operation_name).pascal())
                occasion = Operation
                if f"actions.{key}.{operation_name}" not in steps:
                    raise ValueError(f"actions.{key}.operations.{operation_name} is never run by the orchestrator, so nothing reaches it")
                request_record = self._messages[("relays", Operation + "Request")]
                response_record = self._messages[("relays", Operation + "Response")]
                calls = str(operation.get("calls", ""))
                if calls not in self._port_ops[port_name]:
                    raise ValueError(f"actions.{key}.operations.{operation_name} calls {calls or 'nothing'}, which {port_name} does not declare")
                Call = str(Word(calls).pascal())
                port_request = self._messages[("ports", Call + "Request")]
                port_response = self._messages[("ports", Call + "Response")]
                sources = Sources(SourcesSpec(name=operation_name))
                sources.hold(Source(SourceSpec(
                    expr=operation_name + "_request", type_ref=f"relays.{Operation}Request", kind="plain",
                    prefix=operation_name + "_request.",
                    holds=tuple((str(t.field()), str(self._samples.value(t))) for t in request_record.targets()))))
                statements: list[dict[str, object]] = []
                checks: list[dict[str, object]] = []
                if "builds" in operation:
                    builds = True
                    ask = Ask(AskSpec(name=f"MapTo{Aggregate}Spec", target_ref=f"domain.{Aggregate}Spec", allow_empty=True, occasion=occasion))
                    for target in self._domain_targets[Aggregate + "Spec"]:
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    mapped = mappers.map(ask)
                    statements.append(dict(blank, build=[{}], argument=str(mapped.call())))
                    sources.hold(Source(SourceSpec(expr=aggregate, type_ref=f"domain.{Aggregate}", kind="aggregate",
                                                   prefix=aggregate + ".", holds=tuple(self._readout.of(mapped.values())))))
                if port_request.targets():
                    ask = Ask(AskSpec(name=f"MapTo{Call}Request", target_ref=f"ports.{Call}Request", allow_empty=False, occasion=occasion))
                    for target in port_request.targets():
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    port_mapped = mappers.map(ask)
                    argument = str(port_mapped.call())
                else:
                    port_mapped = Mapped(MappedSpec(call="", values=()))
                    argument = f"ports.{Call}Request()"
                local = calls + "_response"
                assign = f"{local} = " if port_response.targets() else ""
                if store:
                    call_statement = dict(blank, store_call=[{}], holder=holder, repository=str(Word(port_name).snake()),
                                          assign=assign, call=calls, argument=argument)
                else:
                    call_statement = dict(blank, port_call=[{}], holder=holder, assign=assign, call=calls, argument=argument)
                command_section: list[dict[str, object]] = []
                answer = ""
                commands = list(operation.get("commands", []))
                if commands:
                    if len(commands) != 1 or "builds" not in operation:
                        raise ValueError(f"{operation_name} gives one command to the aggregate it builds, because an action decides once")
                    commanded = True
                    command = str(commands[0])
                    if command not in self._commands:
                        raise ValueError(f"{operation_name} gives {command}, which the aggregate does not declare")
                    if "calls_on" not in operation:
                        raise ValueError(f"actions.{key}.operations.{operation_name} matches the outcomes of {command} and does not say which of them calls {calls} (calls_on)")
                    for outcome in operation["calls_on"]:
                        if outcome not in self._commands[command].get("outcomes", []):
                            raise ValueError(f"actions.{key}.operations.{operation_name} calls_on names {str(outcome)!r}, which is not an outcome of {command}")
                    Command = str(Word(command).pascal())
                    ask = Ask(AskSpec(name=f"MapTo{Command}Spec", target_ref=f"domain.{Command}Spec", allow_empty=False, occasion=occasion))
                    for target in self._domain_targets[Command + "Spec"]:
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    command_argument = str(mappers.map(ask).call())
                    ask = Ask(AskSpec(name=f"MapTo{Operation}Response", target_ref=f"relays.{Operation}Response", allow_empty=False, occasion=occasion))
                    for target in response_record.targets():
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    answered = mappers.map(ask)
                    arms = [
                        {"Outcome": Command + "Outcome", "MEMBER": str(outcome).upper(),
                         "calls": [call_statement] if outcome in operation["calls_on"] else [], "answer": str(answered.call())}
                        for outcome in self._commands[command]["outcomes"]
                    ]
                    command_section.append({"command": command, "command_argument": command_argument, "arms": arms})
                    test_name = f"{operation_name}_answers_for_the_{aggregate}_it_builds"
                else:
                    statements.append(call_statement)
                    if port_response.targets():
                        sources.hold(Source(SourceSpec(expr=local, type_ref=f"ports.{Call}Response", kind="plain",
                                                       prefix=local + ".", holds=tuple(self._fakes[("ports", Call + "Response1")].values()))))
                    ask = Ask(AskSpec(name=f"MapTo{Operation}Response", target_ref=f"relays.{Operation}Response", allow_empty=False, occasion=occasion))
                    for target in response_record.targets():
                        ask.target(target)
                    for held in sources.held():
                        ask.source(held)
                    answered = mappers.map(ask)
                    answer = str(answered.call())
                    pairs = port_mapped.values()
                    fake = "fake_" + (str(Word(store).snake()) if store else str(Word(port_name).snake()))
                    if not store and port_request.targets() and all(str(value) != UNKNOWN for _, value in pairs):
                        reads = ", ".join(f"received.{t.field()}" for t in port_request.targets())
                        expected = ", ".join(str(Sample(str(pairs.get(str(t.field())))).literal(t)) for t in port_request.targets())
                        checks.append({"check": f"[({reads},) for received in {fake}.{calls}_requests] == [({expected},)]"})
                    test_name = (f"{operation_name}_answers_for_the_{aggregate}_it_builds" if "builds" in operation
                                 else f"{operation_name}_asks_its_port_and_answers_what_it_said")
                for target in response_record.targets():
                    value = str(answered.values().get(str(target.field())))
                    if value != UNKNOWN:
                        checks.append({"check": f"{operation_name}_response.{target.field()} == {Sample(value).literal(target)}"})
                operations.append({"operation": operation_name, "Operation": Operation, "statements": statements,
                                   "command": command_section, "answer": answer})
                fake_local = "fake_" + holder
                tests.append({
                    "name": test_name, "operation": operation_name, "Operation": Operation,
                    "fake_locals": [{"local": fake_local, "construct": f"Fake{store or port_name}()"}],
                    "dependency_arg": fake_local, "checks": checks,
                    "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request_record.targets()),
                })
            fake_ports: list[dict[str, object]] = []
            fake_stores: list[dict[str, object]] = []
            if store:
                fake_stores.append(self._frames[("store", port_name)] if ("store", port_name) in self._frames else {})
            else:
                fake_ports.append({"Port": port_name, "operations": [
                    {"operation": op, "Operation": str(Word(op).pascal()),
                     "fake_response": str(self._fakes[("ports", str(Word(op).pascal()) + "Response1")].call())}
                    for op in self._port_ops[port_name]]})
            rendered.append({
                "module": str(Word(Actions).snake()), "Actions": Actions, "ApplicationClient": Key + "ApplicationClient",
                "dependency": holder, "dependency_class": store or port_name,
                "mappers": [{"Mapper": str(made.name()), "target": str(made.target()),
                             "params": [{"param": param, "param_type": param_type} for param, param_type in made.params()],
                             "args": [{"field": field, "expr": expr} for field, expr in made.args()]}
                            for made in mappers.defs()],
                "commanded": [{}] if commanded else [], "builds": [{}] if builds else [], "operations": operations,
                "fake_ports": fake_ports, "fake_stores": fake_stores, "fake_relays": [], "actions_tests": tests,
                "stores_faked": [{}] if fake_stores else [],
                "key": str(key), "Port": port_name,
            })
        self._binding["actions"] = rendered
        self._binding["application_exports"] = sorted(
            [{"module": str(a["module"]), "name": str(a["Actions"])} for a in rendered] +
            [{"module": aggregate + "_service", "name": Aggregate + "Service"}],
            key=str,
        )

    def orchestrator(self) -> None:
        Orchestrator = self._Orchestrator
        orchestrators: list[dict[str, object]] = []
        for operation_name, operation in self._composition.get("orchestrator", {}).get("operations", {}).items():
            Operation = str(Word(operation_name).pascal())
            request_record = self._messages[("relays", Operation + "Request")]
            response_record = self._messages[("relays", Operation + "Response")]
            mappers = Mappers(MappersSpec(module=str(Word(Orchestrator).snake())))
            sources = Sources(SourcesSpec(name=operation_name))
            sources.hold(Source(SourceSpec(
                expr=operation_name + "_request", type_ref=f"relays.{Operation}Request", kind="plain",
                prefix=operation_name + "_request.",
                holds=tuple((str(t.field()), str(self._samples.value(t))) for t in request_record.targets()))))
            dependencies: list[dict[str, object]] = []
            statements: list[dict[str, object]] = []
            checks: list[dict[str, object]] = []
            journal: list[str] = []
            steps: list[tuple[str, str, str]] = []
            for step in operation.get("steps", []):
                kind, rest = str(step).split(".", 1)
                if kind == "actions":
                    key, action = rest.split(".", 1)
                    if key not in self._composition.get("actions", {}) or \
                            action not in self._composition["actions"][key].get("operations", {}):
                        raise ValueError(f"step {step} names an action that [actions] does not declare")
                    Relay = str(Word(key).pascal()) + "ActionsRelay"
                    Step = str(Word(action).pascal())
                    call = f"run_{action}"
                    local = action + "_response"
                    target_name = Step + "Request"
                    returned_name = Step + "Response"
                    steps.append((str(key), action, Relay))
                elif kind == "signal":
                    if not rest.startswith("await_"):
                        raise ValueError(f"step {step} is a signal step that does not await")
                    signal = rest.removeprefix("await_")
                    Relay = Orchestrator + "SignalRelay"
                    Step = str(Word(signal).pascal())
                    call = rest
                    local = rest + "_response"
                    target_name = f"Await{Step}Request"
                    returned_name = f"Await{Step}Response"
                else:
                    raise ValueError(f"orchestrator step {step} is of a kind this renderer does not know: {kind}")
                holder = str(Word(Relay).snake())
                dependency: dict[str, object] = {"dependency": holder, "dependency_type": f"relays.{Relay}"}
                if dependency not in dependencies:
                    dependencies.append(dependency)
                target_record = self._messages[("relays", target_name)]
                ask = Ask(AskSpec(name=f"MapTo{target_name}", target_ref=f"relays.{target_name}", allow_empty=False))
                for target in target_record.targets():
                    ask.target(target)
                for held in sources.held():
                    ask.source(held)
                mapped = mappers.map(ask)
                statements.append({"assign": f"{local} = ", "holder": holder, "call": call, "argument": str(mapped.call())})
                pairs = mapped.values()
                if target_record.targets() and all(str(value) != UNKNOWN for _, value in pairs):
                    reads = ", ".join(f"received.{t.field()}" for t in target_record.targets())
                    expected = ", ".join(str(Sample(str(pairs.get(str(t.field())))).literal(t)) for t in target_record.targets())
                    checks.append({"check": f"[({reads},) for received in fake_{holder}.received "
                                            f"if isinstance(received, relays.{target_name})] == [({expected},)]"})
                returned = self._messages[("relays", returned_name)]
                echoed = Ask(AskSpec(name=returned_name, target_ref=returned_name, allow_empty=False))
                for target in returned.targets():
                    echoed.target(target)
                echoed.source(Source(SourceSpec(expr="sent", type_ref="sent", kind="plain", prefix="sent.", holds=tuple(pairs))))
                sources.hold(Source(SourceSpec(expr=local, type_ref=f"relays.{returned_name}", kind="plain", prefix=local + ".",
                                               holds=tuple(self._echo[0].of(echoed).values()))))
                journal.append(call)
            ask = Ask(AskSpec(name=f"MapTo{Operation}Response", target_ref=f"relays.{Operation}Response", allow_empty=False))
            for target in response_record.targets():
                ask.target(target)
            for held in sources.held():
                ask.source(held)
            answered = mappers.map(ask)
            for target in response_record.targets():
                value = str(answered.values().get(str(target.field())))
                if value != UNKNOWN:
                    checks.append({"check": f"{operation_name}_response.{target.field()} == {Sample(value).literal(target)}"})
            fake_relays = []
            for dependency in dependencies:
                Relay = str(dependency["dependency_type"]).removeprefix("relays.")
                fake_relays.append({
                    "Relay": Relay, "journaled": [{}], "watches_store": [],
                    "received_type": " | relays.".join(request for _, _, request, _, _ in self._relay_ops[Relay]),
                    "operations": [
                        {"method": method, "param": param, "Request": request, "Returns": returns,
                         "fake_response": str(self._fakes[("relays", returns + "0")].call())}
                        for method, param, request, returns, _ in self._relay_ops[Relay]
                    ],
                })
            orchestrators.append({
                "module": str(Word(Orchestrator).snake()), "Orchestrator": Orchestrator,
                "ApplicationClient": Orchestrator + "ApplicationClient",
                "mappers": [{"Mapper": str(made.name()), "target": str(made.target()),
                             "params": [{"param": param, "param_type": param_type} for param, param_type in made.params()],
                             "args": [{"field": field, "expr": expr} for field, expr in made.args()]}
                            for made in mappers.defs()],
                "dependencies": dependencies,
                "operations": [{"operation": operation_name, "Operation": Operation, "statements": statements,
                                "answer": str(answered.call())}],
                "operation": operation_name, "Operation": Operation,
                "fake_ports": [], "fake_stores": [], "fake_relays": fake_relays,
                "fake_locals": [{"local": "fake_" + str(d["dependency"]), "construct": f"Fake{str(d['dependency_type']).removeprefix('relays.')}(journal)"}
                                for d in dependencies],
                "orchestrator_args": ", ".join("fake_" + str(d["dependency"]) for d in dependencies),
                "journal_expected": ", ".join(f'"{call}"' for call in journal),
                "checks": checks,
                "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request_record.targets()),
            })
            self._orchestration = (operation_name, steps)
            self._orchestrator_dependencies = dependencies
        self._binding["orchestrators"] = orchestrators

    def publish(self) -> None:
        ports: list[dict[str, object]] = []
        ports_exports: list[dict[str, object]] = []
        for port_name, operations in self._port_ops.items():
            module = str(Word(port_name).snake())
            records = [self._frames[("ports", str(r.name()))] for r in self._packages["ports"].declared(Word(module))]
            store = self._stores.get(port_name, "")
            ports.append({"module": module, "Port": port_name, "records": records, "store": [{}] if store else [],
                          "Store": store,
                          "operations": [{"operation": op, "Operation": str(Word(op).pascal())} for op in operations]})
            names = sorted([str(r["Record"]) for r in records] + [port_name] + ([store] if store else []))
            ports_exports.extend({"module": module, "name": name} for name in names)
        self._binding["ports"] = ports
        self._binding["ports_exports"] = ports_exports
        relays: list[dict[str, object]] = []
        relays_exports: list[dict[str, object]] = []
        signal_module = str(Word(self._Orchestrator).snake()) + "_signal_relay"
        for Relay, relay_operations in self._relay_ops.items():
            module = str(Word(Relay).snake())
            records = [self._frames[("relays", str(r.name()))] for r in self._packages["relays"].declared(Word(module))]
            promises = [{"PROMISE": str(Word(operation).upper()) + "_PROMISE", "promise": operation}
                        for _, _, _, _, operation in relay_operations] if module == signal_module else []
            relays.append({
                "module": module, "Relay": Relay, "promises": promises, "records": records,
                "operations": [{"method": method, "param": param, "Request": request, "Returns": returns}
                               for method, param, request, returns, _ in relay_operations],
            })
            names = [str(p["PROMISE"]) for p in promises]
            for record in records:
                names.append(str(record["Record"]))
                if record["snapshot"]:
                    names.append(str(record["Record"]) + "Snapshot")
            names.append(Relay)
            relays_exports.extend({"module": module, "name": name} for name in names)
        self._binding["relays"] = relays
        self._binding["relays_exports"] = relays_exports
        client_records = [self._frames[("client", str(r.name()))] for r in self._packages["client"].declared(Word("client"))]
        self._binding["client_records"] = client_records
        self._binding["client_operations"] = [
            {"operation": str(operation_name), "Operation": str(Word(str(operation_name)).pascal())}
            for operation_name in self._composition.get("client", {}).get("operations", {})
        ]
        self._binding["client_exports"] = [
            {"name": name}
            for name in sorted([str(r["Record"]) for r in client_records]
                               + [str(self._binding["ClientClass"]), str(self._binding["Rejected"]), "ERRORS"])
        ]
        fake_ports: list[dict[str, object]] = []
        fake_stores: list[dict[str, object]] = []
        fake_relays: list[dict[str, object]] = []
        locals_: list[tuple[str, str, str]] = []
        dependencies = self._binding.get("dependencies", [])
        store_dependency = ""
        for dependency in dependencies if isinstance(dependencies, list) else []:
            dependency_type = str(dependency["dependency_type"])
            if dependency_type.endswith("Store"):
                store_dependency = str(dependency["dependency"])
        for dependency in dependencies if isinstance(dependencies, list) else []:
            name = str(dependency["dependency"])
            type_name = str(dependency["dependency_type"]).split(".", 1)[1]
            if type_name == self._Orchestrator + "Relay":
                fake: dict[str, object] = {
                    "Relay": type_name, "journaled": [], "watches_store": [{}] if store_dependency else [],
                    "received_type": " | relays.".join(request for _, _, request, _, _ in self._relay_ops[type_name]),
                    "operations": [{"method": method, "param": param, "Request": request, "Returns": returns,
                                    "fake_response": str(self._fakes[("relays", returns + "0")].call())}
                                   for method, param, request, returns, _ in self._relay_ops[type_name]],
                }
                if store_dependency:
                    store_port = next(port for port, store in self._stores.items() if str(Word(store).snake()) == store_dependency)
                    fake["Record"] = self._frames[("store", store_port)]["Record"]
                fake_relays.append(fake)
                construct = f"Fake{type_name}(fake_{store_dependency}.{Word(self._aggregate).plural()})" if store_dependency else f"Fake{type_name}()"
                locals_.append(("fake_" + name, construct, "1"))
            elif type_name in self._port_ops:
                fake_ports.append({"Port": type_name, "operations": [
                    {"operation": op, "Operation": str(Word(op).pascal()),
                     "fake_response": str(self._fakes[("ports", str(Word(op).pascal()) + "Response1")].call())}
                    for op in self._port_ops[type_name]]})
                locals_.append(("fake_" + name, f"Fake{type_name}()", "0"))
            else:
                store_port = next(port for port, store in self._stores.items() if store == type_name)
                fake_stores.append(self._frames[("store", store_port)])
                locals_.append(("fake_" + name, f"Fake{type_name}()", "0"))
        self._binding["fake_ports"] = fake_ports
        self._binding["fake_stores"] = fake_stores
        self._binding["fake_relays"] = fake_relays
        fake_locals = [{"local": local, "construct": construct} for local, construct, later in locals_ if later == "0"] + \
                      [{"local": local, "construct": construct} for local, construct, later in locals_ if later == "1"]
        service_args = ", ".join("fake_" + str(d["dependency"]) for d in (dependencies if isinstance(dependencies, list) else []))
        self._binding["service_tests"] = [
            dict(test, fake_locals=fake_locals, service=str(Word(self._Aggregate + "Service").snake()), service_args=service_args)
            for test in self._service_tests
        ]

    def stub(self) -> None:
        Aggregate = self._Aggregate
        aggregate = self._aggregate
        types = self._types
        self._binding["enums"] = [
            {"Enum": name, "enum_snake": str(Word(name).snake()),
             "members": [{"MEMBER": member.upper(), "value": member} for member in members]}
            for name, members in self._enums.items()
        ]
        specs: list[dict[str, object]] = []
        seen: set[str] = set()
        wanted = [(Aggregate + "Spec", self._spec_fields)] + [
            (str(Word(str(command)).pascal()) + "Spec", [(str(f), str(t)) for f, t in table.get("takes", {}).items()])
            for command, table in self._commands.items()
        ]
        ordered: list[tuple[str, list[tuple[str, str]]]] = []
        for spec_name, fields in wanted:
            for field, type_text in fields:
                if str(types.kind(type_text)) == "array":
                    element = str(types.element(type_text))
                    element_spec = element if element.endswith("Spec") else element + "Spec"
                    if element_spec not in seen:
                        seen.add(element_spec)
                        ordered.append((element_spec, list(types.fields(element))))
        for spec_name, fields in wanted[1:] + wanted[:1]:
            if spec_name not in seen:
                seen.add(spec_name)
                ordered.append((spec_name, fields))
        for spec_name, fields in ordered:
            specs.append({"Spec": spec_name, "no_fields": [] if fields else [{}], "fields": [
                {"field": field, "spec_type": (
                    f"tuple[{str(types.element(type_text)) if str(types.element(type_text)).endswith('Spec') else str(types.element(type_text)) + 'Spec'}, ...]"
                    if str(types.kind(type_text)) == "array" else type_text)}
                for field, type_text in fields]})
        self._binding["domain_specs"] = specs
        commands: list[dict[str, object]] = []
        for command, table in self._commands.items():
            outcomes = [str(outcome) for outcome in table.get("outcomes", [])]
            if not outcomes:
                raise ValueError(f"command {command} names no outcomes")
            Command = str(Word(str(command)).pascal())
            targets = self._domain_targets[Command + "Spec"]
            commands.append({
                "command": str(command), "Spec": Command + "Spec", "Outcome": Command + "Outcome",
                "outcomes": [{"MEMBER": outcome.upper()} for outcome in outcomes], "answer": outcomes[0].upper(),
                "command_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in targets),
            })
        self._binding["commands"] = commands
        spec_types = dict(self._spec_fields)
        views: list[dict[str, object]] = []
        leaves: set[str] = set()
        stored: list[dict[str, object]] = []
        read_checks: list[dict[str, object]] = []
        stored_names: set[str] = set()
        for field, type_text in self._spec_fields:
            kind = str(types.kind(type_text))
            read_type = self._read_types.get(field)
            if kind == "scalar" and read_type == type_text:
                stored.append({"field": field, "stored_expr": f"spec.{field}"})
                stored_names.add(field)
                read_checks.append({"actual": f"{'int' if type_text == 'int' else 'str'}({aggregate}.{field})",
                                    "expected": str(self._samples.value(Target(TargetSpec(
                                        field=field, type_text=type_text, kind=kind, package="domain", record="",
                                        element=(), members=()))))})
            elif kind == "array" and read_type is not None and str(types.kind(read_type)) == "array":
                view = str(types.element(read_type))
                element = str(types.element(type_text))
                element_types = dict(types.fields(element))
                view_fields: list[dict[str, object]] = []
                for view_field, _ in types.fields(view):
                    if view_field not in element_types:
                        raise ValueError(f"{view}.{view_field} is read, and {element} does not hold it")
                    held = element_types[view_field]
                    leaves.add("Number" if held == "int" else "Text")
                    view_fields.append({"field": view_field, "leaf": "Number" if held == "int" else "Text", "cast": "int" if held == "int" else "str",
                                        "text_expr": f"spec.{view_field}.value" if str(types.kind(held)) == "enum" else f"spec.{view_field}"})
                element_spec = element if element.endswith("Spec") else element + "Spec"
                views.append({"View": view, "Spec": element_spec, "fields": view_fields})
                var = str(Word(field).singular())
                stored.append({"field": field, "stored_expr": f"tuple({view}({var}) for {var} in spec.{field})"})
                stored_names.add(field)
                sample = json.loads(str(self._samples.value(Target(TargetSpec(
                    field=field, type_text=type_text, kind=kind, package="domain", record=element_spec,
                    element=tuple(types.fields(element)), members=())))))
                view_reads = ", ".join(f"{entry['cast']}({var}.{entry['field']})" for entry in view_fields)
                expected = ", ".join("(" + ", ".join(json.dumps(item[str(entry["field"])]) for entry in view_fields) + ",)" for item in sample)
                read_checks.append({"actual": f"[({view_reads},) for {var} in {aggregate}.{field}]", "expected": f"[{expected}]"})
        if self._identity not in stored_names or spec_types.get(self._identity) != "str":
            raise ValueError(f"the aggregate's identity {self._identity} is a str its spec holds and it reads")
        reads: list[dict[str, object]] = []
        for read, read_type in self._reads:
            kind = str(types.kind(read_type))
            if read in stored_names:
                reads.append({"read": read, "read_type": f"tuple[{types.element(read_type)}, ...]" if kind == "array" else read_type,
                              "read_expr": f"self._{read}"})
            elif kind == "enum":
                first = self._enums[read_type][0].upper()
                reads.append({"read": read, "read_type": "Text", "read_expr": f"Text({read_type}.{first}.value)"})
            elif kind == "array":
                reads.append({"read": read, "read_type": f"tuple[{types.element(read_type)}, ...]", "read_expr": "()"})
            elif read_type == "int":
                reads.append({"read": read, "read_type": "int", "read_expr": "0"})
            else:
                reads.append({"read": read, "read_type": "Text", "read_expr": 'Text("")'})
        self._binding["views"] = views
        self._binding["stored"] = stored
        self._binding["reads"] = reads
        self._binding["identity_type"] = "str"
        self._binding["stub_text"] = [{}] if "Text" in leaves or any(r["read_type"] == "Text" for r in reads) else []
        self._binding["stub_number"] = [{}] if "Number" in leaves else []
        self._binding["serialized"] = [{}] if self._binding["stub_text"] or self._binding["stub_number"] else []
        exports = {Aggregate, Aggregate + "Spec"} | {str(s["Spec"]) for s in specs} | set(self._enums) | {str(c["Outcome"]) for c in commands}
        self._binding["domain_exports"] = [{"name": name} for name in sorted(exports)]
        spec_parts = []
        bare_parts = []
        for target in self._domain_targets[Aggregate + "Spec"]:
            spec_parts.append(f"{target.field()}={self._samples.value(target).literal(target)}")
            bare_parts.append(f"{target.field()}=()" if str(target.kind()) == "array" else f"{target.field()}={self._samples.value(target).literal(target)}")
        self._binding["spec_sample"] = ", ".join(spec_parts)
        self._binding["spec_sample_bare"] = ", ".join(bare_parts)
        self._binding["read_checks"] = read_checks
        self._binding["enum_reads"] = [
            {"read": read, "Enum": read_type, "enum_snake": str(Word(read_type).snake())}
            for read, read_type in self._reads if str(types.kind(read_type)) == "enum"
        ]

    def engine(self) -> None:
        implementations = self._implementations
        Orchestrator = self._Orchestrator
        infra = self._infra
        engines = infra.get("engine", {})
        if self._engine_declared and list(engines) != ["restate"]:
            raise ValueError("infra.toml names an engine other than restate, the one this renderer renders")
        engine = engines.get("restate", {})
        for key in ("engine_url_variable", "engine_path") if self._engine_declared else ():
            if key not in engine:
                raise ValueError(f"[engine.restate] does not say {'where its endpoint is mounted' if key == 'engine_path' else 'which variable is the ' + key.removesuffix('_variable').replace('_', ' ')}")
            self._binding[key] = str(engine[key])
        for key in ("admin_variable", "callback_host_variable"):
            if key in engine:
                raise ValueError(f"[engine.restate] names {key}, which nothing reads: the tests take the engine's admin URL "
                                 f"and callback host from the root conftest's fixtures, so infra.toml names no variable for them")
        self._binding["restate_engine"] = [{}] if self._engine_declared else []
        chosen: dict[str, str] = {}
        if not implementations.get("environments"):
            raise ValueError("implementations.toml declares no [environments]")
        for environment_name, environment in implementations.get("environments", {}).items():
            for port_name in self._port_ops:
                if port_name not in environment.get("implementations", {}):
                    raise ValueError(f"environment {environment_name} names no implementation for {port_name}")
            for port_name, implementation in environment.get("implementations", {}).items():
                if chosen.setdefault(str(port_name), str(implementation)) != str(implementation):
                    raise ValueError(f"{port_name} is {chosen[str(port_name)]} in one environment and {implementation} in "
                                     f"{environment_name}, which needs a selector variable this renderer does not render")
            if self._engine_declared and environment.get("engine") != "restate":
                raise ValueError(f"environment {environment_name} runs no restate engine")
            if not self._engine_declared and "engine" in environment:
                raise ValueError(f"environment {environment_name} runs the {environment['engine']} engine, and infra.toml declares "
                                 f"no [engine]")
            if list(environment.get("hosts", [])) != ["http"]:
                raise ValueError(f"environment {environment_name} serves hosts other than http, the one this renderer renders")
        host = infra.get("hosts", {}).get("http")
        if host is None:
            raise ValueError("infra.toml declares no [hosts.http]")
        self._binding["listen_port_variable"] = str(host["listen_port_variable"])
        storages = {str(name): dict(storage) for name, storage in infra.get("storage", {}).items()}
        for storage_name, storage in storages.items():
            if storage_name != "memory" and "location_variable" not in storage:
                raise ValueError(f"[storage.{storage_name}] names no location_variable: every storage but memory says which "
                                 f"variable locates it")
        port_exprs: dict[str, str] = {}
        shared_stores: list[dict[str, object]] = []
        memory_repositories: list[dict[str, object]] = []
        uuid_repositories: list[dict[str, object]] = []
        gateways: list[dict[str, object]] = []
        agent_stores: list[dict[str, object]] = []
        locations: list[dict[str, object]] = []
        seeded = False
        for port_name, operations in self._port_ops.items():
            if port_name not in chosen:
                raise ValueError(f"no environment says what implements {port_name}")
            key = chosen[port_name]
            implementation = implementations.get("implementations", {}).get(port_name, {}).get(key)
            if implementation is None:
                raise ValueError(f"{port_name} is implemented by {key}, which [implementations.{port_name}] does not declare")
            if port_name in self._stores and key not in storages:
                raise ValueError(f"{port_name} is a store implemented by {key}, a storage infra.toml does not declare: declare "
                                 f"[storage.{key}] in infra.toml, or implement {port_name} by a declared storage")
            body = implementation.get("body")
            if body == "agent":
                if "class" not in implementation:
                    raise ValueError(f"[implementations.{port_name}.{key}] is the agent's and names no class")
                if port_name in self._stores:
                    Store = str(implementation["class"])
                    location_variable = storages[key].get("location_variable")
                    location_attr = f"{key}_location"
                    if location_variable is not None and not any(entry["location_attr"] == location_attr for entry in locations):
                        locations.append({"location_attr": location_attr, "location_variable": str(location_variable)})
                    agent_stores.append(dict(
                        self._frames[("store", port_name)], module=str(Word(Store).snake()), Repository=Store + "Transaction", Store=Store,
                        store=str(Word(Store).snake()), repository=str(Word(port_name).snake()),
                        located=[{}] if location_variable is not None else [],
                    ))
                    shared_stores.append({
                        "store_attr": str(Word(Store).snake()),
                        "store_expr": f"repositories.{Store}(location=config.{location_attr})" if location_variable is not None
                        else f"repositories.{Store}()",
                    })
                    port_exprs[port_name] = f"self._{Word(Store).snake()}"
                    continue
                Gateway = str(implementation["class"])
                gateway_operations: list[dict[str, object]] = []
                for operation in operations:
                    Operation = str(Word(operation).pascal())
                    response = self._messages[("ports", Operation + "Response")]
                    request = self._messages[("ports", Operation + "Request")]
                    gateway_operations.append({
                        "operation": operation, "Operation": Operation,
                        "minimal": ", ".join(
                            f"{t.field()}=()" if str(t.kind()) == "array" else f"{t.field()}={'0' if str(t.type_text()) == 'int' else chr(34) * 2}"
                            for t in response.targets()),
                        "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request.targets()),
                    })
                gateways.append({"module": str(Word(Gateway).snake()), "Gateway": Gateway, "operations": gateway_operations})
                port_exprs[port_name] = f"gateways.{Gateway}()"
            elif body == "supported" and key == "memory":
                if port_name not in self._stores:
                    raise ValueError(f"{port_name} is memory, which renders a store, and it does not carry {self._aggregate}")
                frame = self._frames[("store", port_name)]
                Store = "Memory" + self._stores[port_name]
                memory_repositories.append(dict(
                    frame, module="memory_" + str(Word(port_name).snake()), Repository="Memory" + port_name, Store=Store,
                    store=str(Word(Store).snake()), repository=str(Word(port_name).snake()),
                ))
                shared_stores.append({"store_attr": str(Word(Store).snake()), "store_expr": f"repositories.{Store}()"})
                port_exprs[port_name] = f"self._{Word(Store).snake()}"
            elif body == "supported" and key == "uuid":
                Operation = str(Word(operations[0]).pascal()) if len(operations) == 1 else ""
                issue_response = self._messages.get(("ports", Operation + "Response"))
                issue_request = self._messages.get(("ports", Operation + "Request"))
                if issue_response is None or issue_request is None or issue_request.targets() or \
                        [str(t.kind()) for t in issue_response.targets()] != ["scalar"]:
                    raise ValueError(f"{port_name} is uuid, which renders one operation that takes nothing and issues one id")
                uuid_repositories.append({
                    "module": "uuid_" + str(Word(port_name).snake()), "Repository": "Uuid" + port_name,
                    "repository": str(Word("Uuid" + port_name).snake()), "issue": operations[0], "Issue": Operation,
                    "issued": str(issue_response.targets()[0].field()),
                })
                port_exprs[port_name] = f"repositories.Uuid{port_name}(config.identity_seed)"
                seeded = True
            else:
                raise ValueError(f"{port_name} is implemented by {key}, a type the toolkit does not support; say body = \"agent\"")
        self._binding["gateways"] = gateways
        self._binding["memory_repositories"] = memory_repositories
        self._binding["agent_stores"] = agent_stores
        self._binding["locations"] = locations
        self._binding["located"] = [{}] if locations else []
        self._binding["uuid_repositories"] = uuid_repositories
        self._binding["shared_stores"] = shared_stores
        self._binding["identity_seeded"] = [{}] if seeded else []
        self._binding["configured"] = [{}] if self._engine_declared or seeded or locations else []
        self._binding["reads_environment"] = [{}] if self._engine_declared or locations else []
        self._port_exprs = port_exprs
        service_args: list[dict[str, object]] = []
        service_dependencies = self._binding.get("dependencies", [])
        for dependency in service_dependencies if isinstance(service_dependencies, list) else []:
            type_name = str(dependency["dependency_type"]).split(".", 1)[1]
            if type_name == Orchestrator + "Relay":
                workflow_local = str(Word("Restate" + str(Word(self._orchestration[0]).pascal())).snake())
                service_args.append({"expr": f"dispatchers.RestateHttp{Orchestrator}Relay(config.engine_url, {workflow_local})"})
            elif type_name in port_exprs:
                service_args.append({"expr": port_exprs[type_name]})
            else:
                service_args.append({"expr": port_exprs[next(port for port, store in self._stores.items() if store == type_name)]})
        self._binding["service_args"] = service_args
        imported = {"activities", "workflows"} if self._engine_declared else set()
        if self._relay_ops.get(Orchestrator + "Relay"):
            imported.add("dispatchers")
        if gateways:
            imported.add("gateways")
        if memory_repositories or uuid_repositories or agent_stores:
            imported.add("repositories")
        self._binding["component_imports"] = [{"package": name} for name in sorted(imported)]

    def restate(self) -> None:
        if not self._engine_declared:
            for name in ("activities", "application_clients", "first_activity", "containers", "workflows", "http_dispatchers"):
                self._binding[name] = []
            return
        identity = self._identity
        Orchestrator = self._Orchestrator
        port_exprs = self._port_exprs
        operation_name, steps = self._orchestration
        activities: list[dict[str, object]] = []
        used: list[str] = []
        for key, action, _ in steps:
            Key = str(Word(key).pascal())
            Actions = Key + "Actions"
            Operation = str(Word(action).pascal())
            request = self._messages[("relays", Operation + "Request")]
            response = self._messages[("relays", Operation + "Response")]
            port_name = str(self._composition["actions"][key]["port"])
            Activity = "Restate" + Operation
            activities.append({
                "Activity": Activity, "activity_param": str(Word(Activity).snake()),
                "container_attr": str(Word(Actions).snake()) + "_service", "container": Actions,
                "application_client": str(Word(Key + "ApplicationClient").snake()), "ApplicationClient": Key + "ApplicationClient",
                "operation": action, "Operation": Operation,
                "serdes": [{"Message": Operation + "Request", "message": action + "_request"},
                           {"Message": Operation + "Response", "message": action + "_response"}],
                "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request.targets()),
                "echo": str(self._fakes[("relays", Operation + "Response0")].call()),
                "response_expected": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in response.targets()),
                "actions_container_attr": str(Word(Actions).snake()) + "_service", "actions_container": Actions,
                "Actions": Actions, "port_expr": port_exprs[port_name],
                "keyed": [{}] if any(str(t.field()) == identity for t in request.targets()) else [],
                "actions_key": key,
            })
            if key not in used:
                used.append(key)
        self._binding["activities"] = activities
        application_clients: list[dict[str, object]] = []
        for activity in activities:
            grouped = next((entry for entry in application_clients if entry["ApplicationClient"] == activity["ApplicationClient"]), None)
            if grouped is None:
                grouped = {"ApplicationClient": activity["ApplicationClient"], "application_client": activity["application_client"],
                           "calls": [], "keyed": [{}]}
                application_clients.append(grouped)
            calls = grouped["calls"]
            if isinstance(calls, list):
                calls.append({"operation": activity["operation"], "Operation": activity["Operation"], "echo": activity["echo"]})
            if not activity["keyed"]:
                grouped["keyed"] = []
        for grouped in application_clients:
            calls = grouped["calls"]
            grouped["received_type"] = " | ".join(
                f"relays.{call['Operation']}Request" for call in (calls if isinstance(calls, list) else []) if isinstance(call, dict))
        self._binding["application_clients"] = application_clients
        self._binding["first_activity"] = activities[:1]
        containers: list[dict[str, object]] = []
        for key in used:
            Actions = str(Word(key).pascal()) + "Actions"
            names = sorted(str(a["operation"]) for a in activities if a["actions_key"] == key)
            containers.append({"container_attr": str(Word(Actions).snake()) + "_service", "container": Actions,
                               "container_kind": "Service", "private_container": [{}],
                               "handler_names": ", ".join(f'"{name}"' for name in names)})
        workflow_attr = str(Word(Orchestrator).snake()) + "_workflow"
        containers.append({"container_attr": workflow_attr, "container": Orchestrator, "container_kind": "Workflow",
                           "private_container": [], "handler_names": f'"{operation_name}"'})
        self._binding["containers"] = containers
        dispatchers: list[dict[str, object]] = []
        awaited: list[dict[str, object]] = []
        for dependency in self._orchestrator_dependencies:
            Relay = str(dependency["dependency_type"]).removeprefix("relays.")
            dispatcher: dict[str, object] = {"Dispatcher": "RestateInvocation" + Relay}
            dispatcher_activities: list[dict[str, object]] = []
            run_methods: list[dict[str, object]] = []
            await_methods: list[dict[str, object]] = []
            for method, param, request_name, returns, operation in self._relay_ops[Relay]:
                if method.startswith("run_"):
                    activity = next(a for a in activities if a["operation"] == operation)
                    dispatcher_activities.append({"activity_param": activity["activity_param"], "Activity": activity["Activity"]})
                    run_methods.append({"method": method, "param": param, "Request": request_name, "Returns": returns,
                                        "activity_param": activity["activity_param"]})
                else:
                    await_methods.append({"method": method, "param": param, "Request": request_name, "Returns": returns,
                                          "PROMISE": str(Word(operation).upper()) + "_PROMISE"})
            dispatcher.update(dispatcher_activities=dispatcher_activities, run_methods=run_methods, await_methods=await_methods)
            awaited.extend(await_methods)
            dispatchers.append(dispatcher)
        Operation = str(Word(operation_name).pascal())
        request = self._messages[("relays", Operation + "Request")]
        keyed = ", ".join(
            f"{identity}=workflow_key" if str(t.field()) == identity else f"{t.field()}={self._samples.value(t).literal(t)}"
            for t in request.targets())
        Workflow = "Restate" + Operation
        workflow: dict[str, object] = {
            "module": str(Word(Workflow).snake()), "Workflow": Workflow, "workflow_param": str(Word(Workflow).snake()),
            "workflow_local": str(Word(Workflow).snake()), "container_attr": workflow_attr,
            "workflow_container_attr": workflow_attr, "workflow_container": Orchestrator,
            "operation": operation_name, "Operation": Operation, "Orchestrator": Orchestrator,
            "serdes": [{"Message": Operation + "Request", "message": operation_name + "_request"},
                       {"Message": Operation + "Response", "message": operation_name + "_response"}],
            "invocation_dispatchers": dispatchers, "workflow_activities": activities,
            "served_containers": ", ".join(str(c["container_attr"]) for c in containers),
            "keyed_request_sample": keyed,
            "awaited_promises": [{"PROMISE": m["PROMISE"]} for m in awaited],
            "awaits": [{}] if awaited else [],
        }
        self._binding["workflows"] = [workflow]
        start_methods = [{"method": method, "param": param, "Request": request_name, "Returns": returns,
                          "result": str(Word(returns).snake())}
                         for method, param, request_name, returns, _ in self._relay_ops[Orchestrator + "Relay"]
                         if method.startswith("start_")]
        run_methods = [{"method": method, "param": param, "Request": request_name, "Returns": returns,
                        "result": str(Word(returns).snake())}
                       for method, param, request_name, returns, _ in self._relay_ops[Orchestrator + "Relay"]
                       if method.startswith("run_")]
        self._binding["http_dispatchers"] = [dict(
            workflow, module="restate_http_" + str(Word(Orchestrator).snake()) + "_relay",
            Dispatcher="RestateHttp" + Orchestrator + "Relay", start_methods=start_methods, run_methods=run_methods,
        )] if start_methods or run_methods else []

    def routes(self) -> None:
        served = [str(story) for story in self._composition.get("interfaces", {}).get("http", {}).get("serves", [])]
        pending: list[dict[str, object]] = list(self._story.get("jtbds", []))
        stories: dict[str, dict[str, object]] = {}
        while pending:
            node = pending.pop()
            stories[str(node.get("id", ""))] = node
            if "reached_by" in node:
                raise ValueError(f"{node.get('id', '')} has reached_by, which is no longer part of the story format; "
                                 "write in its given how it is reached, and write the calls in its root test")
            for child_key in ("jtbds", "stories"):
                children = node.get(child_key, [])
                if isinstance(children, list):
                    pending.extend(child for child in children if isinstance(child, dict))
        routes: list[dict[str, object]] = []
        probes: list[dict[str, object]] = []
        answers: list[str] = []
        routed_stories: set[str] = set()
        answered_by: dict[str, dict[str, object]] = {}
        for operation_name, operation in self._composition.get("client", {}).get("operations", {}).items():
            Operation = str(Word(operation_name).pascal())
            routed = [str(story) for story in operation.get("serves", []) if "route" in stories.get(str(story), {})]
            routed_stories.update(routed)
            if len(routed) != 1:
                raise ValueError(f"client operation {operation_name} serves {len(routed)} level-2 stories with a route; "
                                 "it serves exactly one, whose route it is")
            story = stories[routed[0]]
            if routed[0] not in served:
                raise ValueError(f"{routed[0]} has a route, and [interfaces.http] does not serve it")
            route = ROUTE.fullmatch(str(story.get("route", "")))
            if route is None:
                raise ValueError(f"{routed[0]}'s route is not like \"POST /loans\" (a method, a space, and a path of "
                                 "lowercase segments whose parameters are written {field})")
            status_code = story.get("status")
            if not isinstance(status_code, int) or isinstance(status_code, bool) or not 200 <= status_code < 300:
                raise ValueError(f"{routed[0]} has no status, the 2xx its route answers with, like 201")
            method, path = route.group(1), route.group(2)
            if f"{method} {path}" in answered_by:
                raise ValueError(f"client operations {answered_by[f'{method} {path}']['operation']} and {operation_name} are both "
                                 f"{method} {path}, and HTTP reaches only one of them")
            when = str(story.get("when", ""))
            then = str(story.get("then", ""))
            said = (
                re.search(rf"(?<![A-Za-z]){method}(?![A-Za-z])", when),
                re.search(rf"(?<![A-Za-z0-9_/{{}}-]){re.escape(path)}(?![A-Za-z0-9_/{{}}-])", when),
                re.search(rf"(?<![0-9]){status_code}(?![0-9])", then),
            )
            if not all(said):
                raise ValueError(f"{routed[0]} is {method} {path} answering {status_code}, and its own when and then "
                                 f"do not say so (when: {when!r}; then: {then!r})")
            path_fields = PATH_FIELD.findall(path)
            for repeated in sorted({field for field in path_fields if path_fields.count(field) > 1}):
                raise ValueError(f"{path} names {{{repeated}}} more than once, and a path parameter is bound once")
            request = self._messages[("client", Operation + "Request")]
            response = self._messages[("client", Operation + "Response")]
            inputs: list[dict[str, object]] = []
            body: dict[str, object] = {}
            for target in request.targets():
                field = str(target.field())
                if field in path_fields and str(target.type_text()) not in ("str", "int"):
                    raise ValueError(f"{path} names {{{field}}}, a {target.type_text()}, and a path carries only text or an integer")
                if field in path_fields:
                    inputs.append({"field": field, "reader": "path_param" if str(target.type_text()) == "str" else "integer_path_param"})
                elif str(target.kind()) == "scalar":
                    inputs.append({"field": field, "reader": "text" if str(target.type_text()) == "str" else "integer"})
                    body[field] = json.loads(str(self._samples.value(target)))
                else:
                    raise ValueError(f"{operation_name} takes {field}, which a JSON body does not carry as text")
            for field in path_fields:
                if field not in [str(t.field()) for t in request.targets()]:
                    raise ValueError(f"{path} names {{{field}}}, which {operation_name} does not take")
            path_params = {field: str(json.loads(str(self._samples.value(t)))) for t in request.targets()
                           for field in [str(t.field())] if field in path_fields}
            response_values = {str(t.field()): json.loads(str(self._samples.value(t))) for t in response.targets()}
            answered_by[str(story["route"])] = {
                "operation": operation_name, "method": method, "path": path, "path_fields": path_fields,
                "body": repr(json.dumps(body).encode()) if body else "None",
                "path_types": {str(t.field()): str(t.type_text()) for t in request.targets() if str(t.field()) in path_fields},
                "path_samples": {str(t.field()): str(self._samples.value(t).literal(t)) for t in request.targets()
                                 if str(t.field()) in path_fields},
            }
            routes.append({
                "operation": operation_name, "Operation": Operation, "method": method, "path": path,
                "status": str(status_code), "inputs": inputs, "has_inputs": [{}] if inputs else [],
                "outputs": self._frames[("client", Operation + "Response")]["fields"],
                "response_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in response.targets()),
                "response_json": json.dumps(response_values),
                "request_sample": ", ".join(f"{t.field()}={self._samples.value(t).literal(t)}" for t in request.targets()),
                "path_params_sample": json.dumps(path_params),
                "body_sample": repr(json.dumps(body).encode()) if body else 'b""',
            })
            steps = [str(step) for step in operation.get("steps", [])]
            integers = {str(t.field()) for t in request.targets() if str(t.type_text()) == "int"}
            probe_path = "/".join(
                segment if not PATH_FIELD.fullmatch(segment) else "0" if segment[1:-1] in integers else "never-issued"
                for segment in path.split("/")
            )
            if body:
                probes.append({"method": method, "path": probe_path, "body": 'b"{}"'})
                answers.append("400")
                probes.append({"method": method, "path": probe_path, "body": repr(json.dumps(body).encode())})
                reaches = any(step.startswith("orchestrator.") for step in steps)
                loads = bool(path_fields) and any(step.startswith("repository.") for step in steps)
                answers.append("500" if reaches or loads else str(status_code))
            elif path_fields and any(step.startswith("repository.") for step in steps):
                probes.append({"method": method, "path": probe_path, "body": "None"})
                answers.append("500")
        unserved = sorted(story_id for story_id, story in stories.items() if "route" in story and story_id not in routed_stories)
        if unserved:
            raise ValueError(f"{', '.join(unserved)} has a route, and no client operation serves it")
        root_tests: list[dict[str, object]] = []
        for story_id in sorted(routed_stories):
            story = stories[story_id]
            call = answered_by[str(story["route"])]
            method, path = str(call["method"]), str(call["path"])
            path_types = typing.cast(dict[str, str], call["path_types"])
            path_samples = typing.cast(dict[str, str], call["path_samples"])
            words = "_".join([GERUNDS[method]] + [
                "by_" + segment[1:-1] if PATH_FIELD.fullmatch(segment) else segment.replace("-", "_")
                for segment in path.strip("/").split("/")
            ])
            root_tests.append({
                "module": f"test_{words}", "Words": str(Word(words).pascal()), "story": story_id.replace("-", "_"),
                "method": method, "path": path, "body": call["body"], "status": str(story["status"]),
                "path_values": [{"name": name, "type": kind, "sample": path_samples[name]} for name, kind in path_types.items()],
                "story_text": repr(f"{story_id}: given {story.get('given', '')}; then {story.get('then', '')}"),
            })
        self._binding["root_tests"] = root_tests
        self._binding["root_tier"] = [{}] if root_tests else []
        self._binding["routes"] = routes
        self._binding["route_probes"] = probes
        self._binding["route_probe_answers"] = ", ".join(answers)

    def traced(self) -> None:
        pending: list[dict[str, object]] = list(self._story.get("jtbds", []))
        prose: list[str] = []
        while pending:
            node = pending.pop()
            prose.extend(str(node[key]) for key in ("given", "when", "then") if key in node)
            for child_key in ("jtbds", "stories"):
                children = node.get(child_key, [])
                if isinstance(children, list):
                    pending.extend(child for child in children if isinstance(child, dict))
        text = "\n".join(prose)
        pieces: list[tuple[str, str]] = []
        for enum, members in self._enums.items():
            pieces.extend((f"enum {enum} value {member}", member) for member in members)
        for operation_name, operation in self._composition.get("client", {}).get("operations", {}).items():
            for side in ("request", "response"):
                pieces.extend((f"client operation {operation_name} {side} field {str(field).split(':', 1)[0].strip()}",
                               str(field).split(":", 1)[0].strip())
                              for field in operation.get(side, []))
        pieces.extend((f"aggregate read {field}", field) for field, _ in self._reads)
        for signal_name, signal in self._composition.get("signals", {}).items():
            pieces.extend((f"signal {signal_name} payload field {field}", str(field)) for field in signal.get("payload", []))
        for command, table in self._commands.items():
            pieces.extend((f"command {command} outcome {outcome}", str(outcome)) for outcome in list(table.get("outcomes", []))[1:])
        untraced = [
            f"{piece} is named by no story: write it in a story's given, when, or then, or remove it from the composition"
            for piece, name in pieces
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name).replace("_", "[_ ]") + r"(?![A-Za-z0-9_])", text, re.IGNORECASE) is None
        ]
        if untraced:
            raise ValueError(*untraced)

    def scope(self) -> Scope:
        table: list[str] = []
        indexes: dict[int, int] = {}
        stack: list[tuple[dict[str, object], bool]] = [(self._binding, False)]
        while stack:
            node, done = stack.pop()
            if not done:
                stack.append((node, True))
                for bound in node.values():
                    if isinstance(bound, list):
                        stack.extend((child, False) for child in bound if isinstance(child, dict) and id(child) not in indexes)
                continue
            if id(node) in indexes:
                continue
            frame: dict[str, object] = {}
            for key, bound in node.items():
                if isinstance(bound, str):
                    frame[key] = bound
                elif isinstance(bound, list):
                    frame[key] = [indexes[id(child)] for child in bound if isinstance(child, dict)]
            indexes[id(node)] = len(table)
            table.append(json.dumps(frame))
        return Scope((tuple(table), (indexes[id(self._binding)],)))


class Digest(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        normalized = "\n".join(line.rstrip() for line in value.splitlines()).strip("\n")
        object.__setattr__(self, "_value", hashlib.sha256(normalized.encode()).hexdigest()[:16])

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class LevelSpec(ts.Spec):

    def __init__(
        self,
        path: str,
        mode: str,
        records: tuple[tuple[str, str], ...],
        rendered: tuple[tuple[str, str, str, str, tuple[tuple[str, str, str, str], ...]], ...],
        existing: tuple[tuple[str, str, str, str, tuple[tuple[str, str, str, str], ...]], ...],
    ) -> None:
        self.path = path
        self.mode = mode
        self.records = records
        self.rendered = rendered
        self.existing = existing


class Level(ts.Entity):

    def __init__(self, spec: LevelSpec) -> None:
        self._path = spec.path
        self._kept: list[Text] = []
        self._conflicts: list[Text] = []
        self._drift: list[Text] = []
        records = dict(spec.records)
        wanted = {row[0]: row for row in spec.rendered}
        placed: list[tuple[str, str, str]] = []
        for key, name, lead, text, members in spec.existing:
            whole = text + "".join(member_lead + member_text for _, _, member_lead, member_text in members)
            row = wanted.get(key)
            if row is None:
                untouched = spec.mode == RECORDED and records.get(key) == str(Digest(text)) and all(
                    records.get(member_key) == str(Digest(member_text)) for member_key, _, _, member_text in members
                )
                if untouched and not key.startswith(("import ", "from ")):
                    self._drift.append(Text(f"{spec.path}: {name} is no longer rendered"))
                elif not untouched:
                    self._kept.append(Text(name))
                    placed.append((key, lead, whole))
                continue
            _, rendered_name, _, rendered_text, rendered_members = row
            split = bool(members) and bool(rendered_members)
            rendered_whole = rendered_text + "".join(member_lead + member_text for _, _, member_lead, member_text in rendered_members)
            ours, theirs = (text, rendered_text) if split else (whole, rendered_whole)
            recorded = records.get(key)
            chosen = theirs
            if Digest(ours) == Digest(theirs):
                chosen = theirs
            elif spec.mode == RECORDED and recorded == str(Digest(ours)):
                self._drift.append(Text(f"{spec.path}: {rendered_name} differs from what the composition renders"))
            else:
                chosen = ours
                self._kept.append(Text(name))
                if spec.mode == RECORDED and recorded != str(Digest(theirs)):
                    self._conflicts.append(Text(name))
                    self._drift.append(Text(f"{spec.path}: {name} was edited by hand, and the composition now renders it differently"))
            if split:
                level = Level(LevelSpec(
                    path=spec.path, mode=spec.mode, records=spec.records,
                    rendered=tuple((member_key, member_name, member_lead, member_text, ())
                                   for member_key, member_name, member_lead, member_text in rendered_members),
                    existing=tuple((member_key, member_name, member_lead, member_text, ())
                                   for member_key, member_name, member_lead, member_text in members),
                ))
                self._kept.extend(level.kept())
                self._conflicts.extend(level.conflicts())
                self._drift.extend(level.drift())
                chosen += "".join(str(piece) for piece in level.placed())
            placed.append((key, lead, chosen))
        for index, (key, name, lead, text, members) in enumerate(spec.rendered):
            if any(placed_key == key for placed_key, _, _ in placed):
                continue
            if not key.startswith(("import ", "from ")):
                self._drift.append(Text(f"{spec.path}: {name} is missing"))
            position = 0
            for earlier in reversed(spec.rendered[:index]):
                at = [spot for spot, (placed_key, _, _) in enumerate(placed) if placed_key == earlier[0]]
                if at:
                    position = at[0] + 1
                    break
            placed.insert(position, (key, lead, text + "".join(member_lead + member_text for _, _, member_lead, member_text in members)))
        self._placed = tuple(Text(lead + text) for _, lead, text in placed)

    @property
    def identity(self) -> str:
        return self._path

    def placed(self) -> tuple[Text, ...]:
        return self._placed

    def kept(self) -> tuple[Text, ...]:
        return tuple(self._kept)

    def conflicts(self) -> tuple[Text, ...]:
        return tuple(self._conflicts)

    def drift(self) -> tuple[Text, ...]:
        return tuple(self._drift)


class MergeSpec(ts.Spec):

    def __init__(self, path: str, rendered: str, existing: str, records: tuple[tuple[str, str], ...], mode: str) -> None:
        self.path = path
        self.rendered = rendered
        self.existing = existing
        self.records = records
        self.mode = mode


class Merge(ts.Entity):

    def __init__(self, spec: MergeSpec) -> None:
        self._path = spec.path
        self._kept: list[Text] = []
        self._conflicts: list[Text] = []
        self._drift: list[Text] = []
        self._text = Text(spec.rendered)
        records = dict(spec.records)
        if not spec.path.endswith(".py"):
            self._recorded: tuple[Text, ...] = (Text(f"{Digest(spec.rendered)}\t{spec.path}\t{WHOLE}"),)
            recorded = records.get(WHOLE)
            if Digest(spec.existing) == Digest(spec.rendered):
                return
            if spec.mode == GENERATED or (spec.mode == RECORDED and recorded == str(Digest(spec.existing))):
                self._drift.append(Text(f"{spec.path} differs from what the composition renders"))
                return
            self._text = Text(spec.existing)
            self._kept.append(Text(spec.path))
            if spec.mode == RECORDED and recorded != str(Digest(spec.rendered)):
                self._conflicts.append(Text(spec.path))
                self._drift.append(Text(f"{spec.path} was edited by hand, and the composition now renders it differently"))
            return
        layouts: list[tuple[str, tuple[tuple[str, str, str, str, tuple[tuple[str, str, str, str], ...], bool], ...], str]] = []
        for source in (spec.rendered,) if spec.mode == GENERATED else (spec.rendered, spec.existing):
            try:
                statements = ast.parse(source).body
            except SyntaxError as error:
                raise ValueError(f"line {error.lineno}: {error.msg}") from error
            lines = source.splitlines(keepends=True)
            spots: dict[int, tuple[int, str, str]] = {}
            for statement in [*statements, *(member for top in statements if isinstance(top, ast.ClassDef) for member in top.body)]:
                start = statement.lineno
                if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = min([start] + [decorator.lineno for decorator in statement.decorator_list])
                if isinstance(statement, (ast.Import, ast.ImportFrom)):
                    key = name = ast.unparse(statement)
                elif isinstance(statement, ast.ClassDef):
                    key, name = f"class {statement.name}", statement.name
                elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    key, name = f"def {statement.name}", statement.name
                elif isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                    key, name = f"{statement.targets[0].id} =", statement.targets[0].id
                elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    key, name = f"{statement.target.id} =", statement.target.id
                else:
                    key = name = lines[statement.lineno - 1].strip()
                spots[id(statement)] = (start, key, name)
            first = spots[id(statements[0])][0] if statements else len(lines) + 1
            head = 0
            while head < first - 1 and lines[head].startswith("#"):
                head += 1
            headers: dict[int, int] = {}
            for top in statements:
                if isinstance(top, ast.ClassDef) and spots[id(top.body[0])][0] > top.lineno:
                    header_end = spots[id(top.body[0])][0] - 1
                    while header_end > spots[id(top)][0] and (
                        not lines[header_end - 1].strip() or lines[header_end - 1].lstrip().startswith("#")
                    ):
                        header_end -= 1
                    headers[id(top)] = header_end
            work: list[tuple[list[ast.stmt], int, str, str, int]] = [
                (top.body, headers[id(top)], spots[id(top)][1] + NESTED, spots[id(top)][2] + ".", id(top))
                for top in statements if isinstance(top, ast.ClassDef) and id(top) in headers
            ]
            work.append((statements, head, "", "", 0))
            levels: dict[int, tuple[tuple[str, str, str, str, tuple[tuple[str, str, str, str], ...], bool], ...]] = {}
            for body, after, prefix, owner, owner_id in work:
                rows: list[tuple[str, str, str, str, tuple[tuple[str, str, str, str], ...], bool]] = []
                seen: dict[str, int] = {}
                previous = after
                for statement in body:
                    start, key, name = spots[id(statement)]
                    end = statement.end_lineno or start
                    seen[key] = seen.get(key, 0) + 1
                    if seen[key] > 1:
                        key, name = f"{key} #{seen[key]}", f"{name} #{seen[key]}"
                    text = "".join(lines[start - 1 : headers.get(id(statement), end) if owner_id == 0 else end])
                    members = tuple(row[:4] for row in levels.get(id(statement), ())) if owner_id == 0 else ()
                    rows.append((
                        prefix + key, owner + name, "".join(lines[previous : start - 1]),
                        text if text.endswith("\n") else text + "\n", members,
                        isinstance(statement, (ast.Import, ast.ImportFrom)),
                    ))
                    previous = end
                levels[owner_id] = tuple(rows)
            last = max((statement.end_lineno or 0) for statement in statements) if statements else head
            layouts.append(("".join(lines[:head]), levels[0], "".join(lines[last:])))
        head_text, module_rows, tail = layouts[0]
        self._recorded = (Text(f"{Digest(spec.rendered)}\t{spec.path}\t{WHOLE}"),) + tuple(
            Text(f"{Digest(text)}\t{spec.path}\t{key}")
            for row_key, _, _, row_text, members, _ in module_rows
            for key, text in [(row_key, row_text), *((member_key, member_text) for member_key, _, _, member_text in members)]
        )
        if spec.mode == GENERATED:
            if spec.existing != spec.rendered:
                self._drift.append(Text(f"{spec.path} differs from what the composition renders"))
            return
        pieces: list[str] = [head_text]
        for imported in (True, False):
            level = Level(LevelSpec(
                path=spec.path, mode=spec.mode, records=spec.records,
                rendered=tuple(row[:5] for row in module_rows if row[5] == imported),
                existing=tuple(row[:5] for row in layouts[1][1] if row[5] == imported),
            ))
            self._kept.extend(level.kept())
            self._conflicts.extend(level.conflicts())
            self._drift.extend(level.drift())
            pieces.extend(str(piece) for piece in level.placed())
        if self._kept:
            self._text = Text("".join(pieces) + tail)

    @property
    def identity(self) -> str:
        return self._path

    def text(self) -> Text:
        return self._text

    def kept(self) -> tuple[Text, ...]:
        return tuple(self._kept)

    def conflicts(self) -> tuple[Text, ...]:
        return tuple(self._conflicts)

    def drift(self) -> tuple[Text, ...]:
        return tuple(self._drift)

    def recorded(self) -> tuple[Text, ...]:
        return self._recorded


class RenamingSpec(ts.Spec):

    def __init__(self, before: tuple[tuple[str, str], ...], after: tuple[tuple[str, str], ...]) -> None:
        self.before = before
        self.after = after


class Renaming(ts.ValueObject):

    _pairs: Pairs

    def __init__(self, spec: RenamingSpec) -> None:
        after = dict(spec.after)
        pairs: dict[str, str] = {}
        for role, old in spec.before:
            new = after.get(role, old)
            if new == old or not SNAKE.fullmatch(old) or not SNAKE.fullmatch(new):
                continue
            for spell in (Word.plural, Word.pascal, Word.upper):
                pairs[str(spell(Word(old)))] = str(spell(Word(new)))
            pairs[str(Word(old).plural().pascal())] = str(Word(new).plural().pascal())
            pairs[str(Word(old).plural().upper())] = str(Word(new).plural().upper())
            pairs[old] = new
        object.__setattr__(self, "_pairs", Pairs(tuple(sorted(pairs.items(), key=str, reverse=True))))

    def apply(self, text: str) -> Text:
        olds = sorted((old for old, _ in self._pairs), key=len, reverse=True)
        if not olds:
            return Text(text)
        pattern = re.compile("|".join(
            f"(?<![A-Z0-9]){re.escape(old)}(?![A-Z0-9])" if old.isupper()
            else f"(?<![A-Z]){re.escape(old)}(?![a-z])" if old[:1].isupper()
            else f"(?<![a-z0-9]){re.escape(old)}(?![a-z0-9])"
            for old in olds
        ))
        pieces: list[str] = []
        position = 0
        for match in pattern.finditer(text):
            pieces.append(text[position : match.start()])
            pieces.append(str(self._pairs.get(match.group(0))))
            position = match.end()
        pieces.append(text[position:])
        return Text("".join(pieces))


class RenderedFileSpec(ts.Spec):

    def __init__(self, path: str, content: str) -> None:
        self.path = path
        self.content = content


class RenderedFile(ts.ValueObject):

    _path: Text
    _content: Text

    def __init__(self, spec: RenderedFileSpec) -> None:
        object.__setattr__(self, "_path", Text(spec.path))
        object.__setattr__(self, "_content", Text(spec.content))

    def path(self) -> Text:
        return self._path

    def content(self) -> Text:
        return self._content


class RenderedTreeSpec(ts.Spec):

    def __init__(
        self,
        documents: tuple[tuple[str, str, str], ...],
        pieces: tuple[tuple[str, str], ...],
        target: str,
        existing: tuple[tuple[str, str], ...],
        printed: tuple[str, ...],
        composition: str,
    ) -> None:
        self.documents = documents
        self.pieces = pieces
        self.target = target
        self.existing = existing
        self.printed = printed
        self.composition = composition


class RenderedTree(ts.AggregateRoot):

    def __init__(self, spec: RenderedTreeSpec) -> None:
        found: list[Text] = []
        texts: dict[str, str] = {}
        for name, state, text in spec.documents:
            if state == READ:
                texts[name] = text
            else:
                found.append(Text(f"the composition's {name}.toml is {state}"
                                  + (f", and it says {HOLDS[name]}" if name in HOLDS else "")))
        for name in DOCUMENTS:
            if name not in texts and not any(document == name for document, _, _ in spec.documents):
                found.append(Text(f"the composition has no {name}.toml" + (f", which says {HOLDS[name]}" if name in HOLDS else "")))
        if spec.target == "not_directory":
            found.append(Text("the output directory is a file"))
        rendered: list[RenderedFile] = []
        if not found:
            try:
                model = Model(ModelSpec(
                    language=texts["language"], story=texts["story"], infra=texts["infra"], composition=texts["composition"],
                    implementations=texts["implementations"], generator=texts["generator"],
                ))
                model.messages()
                model.bodies()
                model.actions()
                model.orchestrator()
                model.publish()
                model.stub()
                model.engine()
                model.restate()
                model.routes()
                model.traced()
                scope = model.scope()
                for path, text in spec.pieces:
                    template = Template(path.removesuffix(TEMPLATE_SUFFIX))
                    for placed in template.place(scope):
                        rendered.append(RenderedFile(RenderedFileSpec(
                            path=str(template.unguarded().render(placed)),
                            content=str(Template(text).render(placed)),
                        )))
                named = "\t".join(f"{role}={scope.value(role)}" for role in ("context", "aggregate", "identity"))
                rendered.append(RenderedFile(RenderedFileSpec(path=RENDERED_FROM, content=f"{spec.composition}\nnames\t{named}\n")))
            except KeyError as missing:
                found.append(Text(f"a spec lacks the key {missing.args[0]}"))
            except (ValueError, TypeError) as problem:
                found.extend(Text(str(reported)) for reported in problem.args)
        paths = [str(rendered_file.path()) for rendered_file in rendered]
        for path in sorted(set(paths)):
            if paths.count(path) > 1:
                found.append(Text(f"two pieces render {path}, and a render writes each path once"))
            segments = path.split("/")
            if path.startswith("/") or "\\" in path or any(segment in ("", ".", "..") for segment in segments):
                found.append(Text(f"a piece renders the path {path!r}, which leaves the output directory"))
        self._faults = tuple(found)
        existing = dict(spec.existing)
        records: dict[str, list[tuple[str, str]]] = {}
        before: list[tuple[str, str]] = []
        after: list[tuple[str, str]] = []
        for source, line in [("existing", line) for line in existing.get(RENDERED_FROM, "").splitlines()[1:]] + [
            ("rendered", line) for rendered_file in rendered if str(rendered_file.path()) == RENDERED_FROM
            for line in str(rendered_file.content()).splitlines()[1:]
        ]:
            fields = line.split("\t")
            if fields[0] == "names":
                (before if source == "existing" else after).extend(
                    (field.split("=", 1)[0], field.split("=", 1)[1]) for field in fields[1:] if "=" in field
                )
            elif len(fields) == 3 and source == "existing":
                records.setdefault(fields[1], []).append((fields[2], fields[0]))
        renaming = Renaming(RenamingSpec(before=tuple(before), after=tuple(after)))
        rendered_paths = {str(rendered_file.path()) for rendered_file in rendered}
        carried = {
            str(renaming.apply(path)): path for path in records
            if path not in rendered_paths and path in existing and str(renaming.apply(path)) in rendered_paths
            and str(renaming.apply(path)) not in existing
        }
        written: list[RenderedFile] = []
        kept: list[Text] = []
        drift: list[Text] = []
        recorded: list[str] = []
        composed = ""
        for rendered_file in sorted(rendered, key=str):
            path = str(rendered_file.path())
            content = str(rendered_file.content())
            if path == RENDERED_FROM:
                composed = content
                if path not in existing:
                    drift.append(Text(f"{path} is missing"))
                elif existing[path].split("\n", 1)[0] != content.split("\n", 1)[0]:
                    drift.append(Text(f"{path} differs from what the composition renders"))
                continue
            current = existing.get(path)
            path_records = tuple(records.get(path, []))
            origin = carried.get(path)
            if origin is not None:
                current = str(renaming.apply(existing[origin]))
                if not path.endswith(".py"):
                    path_records = ((WHOLE, str(Digest(content))),) if str(Digest(existing[origin])) != dict(records[origin]).get(WHOLE) else (
                        (WHOLE, str(Digest(current))),)
                else:
                    try:
                        shown = [
                            [tuple(str(line).split("\t")) for line in Merge(MergeSpec(
                                path=path, rendered=text, existing=text, records=(), mode=RECORDED,
                            )).recorded()]
                            for text in (existing[origin], current, content)
                        ]
                    except ValueError as unparsed:
                        found.append(Text(f"{origin} does not parse ({unparsed}), so the render cannot carry what is written in it by hand"))
                        continue
                    last = dict(records[origin])
                    fresh = {row[2]: row[0] for row in shown[2]}
                    path_records = tuple(
                        (moved[2], moved[0]) if last.get(old[2]) == old[0] else (moved[2], fresh[moved[2]])
                        for old, moved in zip(shown[0], shown[1]) if last.get(old[2]) == old[0] or moved[2] in fresh
                    )
                mode = RECORDED
            elif current is None or path in records:
                mode = RECORDED
            elif not current.startswith((GENERATED_MARKER, AGENT_MARKER)) and current != content and not content.startswith(AGENT_MARKER):
                found.append(Text(f"the output directory already has {path}, which is not marked generated, so the renderer will not replace it"))
                drift.append(Text(f"{path} has lost its generated mark"))
                continue
            elif current.startswith(GENERATED_MARKER) and not records:
                mode = GENERATED
            else:
                mode = OWNED
            try:
                merge = Merge(MergeSpec(
                    path=path, rendered=content, existing=content if current is None else current,
                    records=path_records, mode=mode,
                ))
            except ValueError as unparsed:
                found.append(Text(f"{path} does not parse ({unparsed}), so the render cannot keep what is written in it by hand"))
                continue
            recorded.extend(str(line) for line in merge.recorded())
            written.append(RenderedFile(RenderedFileSpec(path=path, content=str(merge.text()))))
            if current is None:
                drift.append(Text(f"{path} is missing"))
                continue
            if content.startswith(GENERATED_MARKER) and not current.startswith(GENERATED_MARKER):
                drift.append(Text(f"{path} has lost its generated mark"))
            drift.extend(merge.drift())
            if merge.kept():
                kept.append(Text(path if origin is None else f"{path}: what was written by hand in {origin}"))
            kept.extend(Text(f"{path}: {name}, written by hand, which the composition now renders differently")
                        for name in merge.conflicts())
        removed: list[Text] = []
        for path in sorted(records):
            if rendered and path not in rendered_paths and path in existing:
                removed.append(Text(path))
                drift.append(Text(f"{path} is no longer rendered"))
        if composed:
            written.append(RenderedFile(RenderedFileSpec(path=RENDERED_FROM, content=composed + "".join(f"{line}\n" for line in recorded))))
        on_disk = {str(rendered_file.path()): rendered_file for rendered_file in written}
        selected: list[str] = []
        for path in spec.printed:
            if "*" in path:
                pattern = re.compile(re.escape(path).replace(r"\*", "[^/]*"))
                matched = sorted(on_disk_path for on_disk_path in on_disk if pattern.fullmatch(on_disk_path))
                if not matched:
                    found.append(Text(f"--print names {path}, which matches nothing the composition renders"))
                selected.extend(matched)
            elif path not in on_disk and path not in paths:
                found.append(Text(f"--print names {path}, which the composition does not render"))
            else:
                selected.append(path)
        self._printed = () if found else tuple(on_disk[path] for path in selected)
        self._problems = tuple(found)
        self._files = () if found else tuple(written)
        self._kept = () if found else tuple(kept)
        self._removed = () if found else tuple(removed)
        self._drift = tuple(drift) if rendered else ()

    @property
    def identity(self) -> Text:
        return Text("rendered-tree")

    def health(self) -> Health:
        return Health.PROBLEMS if self._problems else Health.CLEAN

    def problems(self) -> tuple[Text, ...]:
        return self._problems

    def files(self) -> tuple[RenderedFile, ...]:
        return self._files

    def kept(self) -> tuple[Text, ...]:
        return self._kept

    def removed(self) -> tuple[Text, ...]:
        return self._removed

    def printed(self) -> tuple[RenderedFile, ...]:
        return self._printed

    def drift(self) -> tuple[Text, ...]:
        return self._drift

    def faults(self) -> tuple[Text, ...]:
        return self._faults
