import tesser.adapters.mapper as adapters_mapper
import tesser.application.mapper as application_mapper
import tesser.do_not_use_mapping as mapping


class Target:
    pass


def test_a_plain_class_maps_to_itself() -> None:
    assert mapping.mapped_type(Target) is Target


def test_a_mapper_maps_to_the_target_it_subclasses() -> None:
    class MapToTarget(adapters_mapper.Mapper, Target):
        pass

    class MapToTargetInApplication(application_mapper.Mapper, Target):
        pass

    assert mapping.mapped_type(MapToTarget) is Target
    assert mapping.mapped_type(MapToTargetInApplication) is Target


def test_a_mapper_derived_from_a_mapper_still_maps_to_the_target() -> None:
    class MapToTarget(adapters_mapper.Mapper, Target):
        pass

    class MapToTargetAgain(MapToTarget):
        pass

    assert mapping.mapped_type(MapToTargetAgain) is Target


def test_a_plain_subclass_is_its_own_type_not_its_base() -> None:
    class Special(Target):
        pass

    assert mapping.mapped_type(Special) is Special
