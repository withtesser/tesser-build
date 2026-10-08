import sys

_MAPPER_MODULES = ("tesser.application.mapper", "tesser.adapters.mapper")


def _mappers() -> tuple[type, ...]:
    found: list[type] = []
    for name in _MAPPER_MODULES:
        module = sys.modules.get(name)
        if module is not None:
            found.append(module.Mapper)
    return tuple(found)


def mapped_type(cls: type) -> type:
    mappers = _mappers()
    if not mappers or not issubclass(cls, mappers):
        return cls
    for base in cls.__mro__:
        if not issubclass(base, mappers):
            return base
    return cls
