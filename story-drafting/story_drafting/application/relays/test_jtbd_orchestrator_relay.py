from __future__ import annotations

import pytest

import story_drafting.application.relays as relays
import tesser.errors as errors


class TestWorkThroughJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        work_through_jtbd_request = relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="design a login page, get my sign-off, then build it")

        raw = relays.WorkThroughJtbdRequestSnapshot().serialize(work_through_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "job": "design a login page, get my sign-off, then build it"}'

    def test_a_request_comes_back_equal(self) -> None:
        work_through_jtbd_request_snapshot = relays.WorkThroughJtbdRequestSnapshot()
        work_through_jtbd_request = relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="design a login page, get my sign-off, then build it")

        returned = work_through_jtbd_request_snapshot.deserialize(work_through_jtbd_request_snapshot.serialize(work_through_jtbd_request))

        assert returned == work_through_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "job": "design a login page, get my sign-off, then build it"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.WorkThroughJtbdRequestSnapshot().deserialize(raw)


class TestWorkThroughJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.WorkThroughJtbdResponseSnapshot().serialize(relays.WorkThroughJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        work_through_jtbd_response_snapshot = relays.WorkThroughJtbdResponseSnapshot()
        work_through_jtbd_response = relays.WorkThroughJtbdResponse(jtbd_id="jtbd-1")

        returned = work_through_jtbd_response_snapshot.deserialize(
            work_through_jtbd_response_snapshot.serialize(work_through_jtbd_response)
        )

        assert returned == work_through_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.WorkThroughJtbdResponseSnapshot().deserialize(raw)
