from __future__ import annotations

import json
import urllib.request as urllib_request
import uuid

import tesser.testing as ts


class TestServedApp:

    def test_a_placed_order_answers_with_its_total_priced_through_the_engine(self) -> None:
        order_id = str(uuid.uuid4())
        order = urllib_request.Request(
            f"{ts.served('DURABLE_EXECUTION_HOST')}/orders",
            data=json.dumps({"order_id": order_id, "sku": "gadget", "quantity": 3}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(order, timeout=30) as answer:
            status = answer.status
            placed = json.loads(answer.read())
        assert status == 200
        assert placed == {"order_id": order_id, "total_cents": 3000}

    def test_a_paid_order_answers_with_its_total_and_payment_reference(self) -> None:
        order_id = str(uuid.uuid4())
        purchase = urllib_request.Request(
            f"{ts.served('DURABLE_EXECUTION_HOST')}/purchases",
            data=json.dumps(
                {"order_id": order_id, "sku": "widget", "quantity": 2, "payment_method": "card-4242"}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(purchase, timeout=30) as answer:
            status = answer.status
            paid = json.loads(answer.read())
        assert status == 200
        assert paid == {"order_id": order_id, "total_cents": 500, "payment_reference": "pay-" + order_id}
