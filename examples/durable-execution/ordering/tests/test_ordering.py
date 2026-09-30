from __future__ import annotations

import asyncio
import typing
import uuid

import httpx
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import pytest
import restate

import ordering.client as client
import ordering.component as component


class TestOrderingContext:

    def test_submitting_an_order_with_no_engine_is_a_fault(self) -> None:
        ordering = component.Ordering(component.Config(component.Spec(engine_url="http://127.0.0.1:9")))
        try:
            with pytest.raises(Exception) as excinfo:
                asyncio.run(
                    ordering.client.submit_order(
                        client.SubmitOrderRequest(order_id="o1", sku="widget", quantity=2)
                    )
                )
            assert not isinstance(excinfo.value, client.ERRORS)
        finally:
            ordering.close()

    def test_placing_an_order_with_no_engine_is_a_fault(self) -> None:
        ordering = component.Ordering(component.Config(component.Spec(engine_url="http://127.0.0.1:9")))
        try:
            with pytest.raises(Exception) as excinfo:
                asyncio.run(
                    ordering.client.place_order(
                        client.PlaceOrderRequest(order_id="o1", sku="widget", quantity=2)
                    )
                )
            assert not isinstance(excinfo.value, client.ERRORS)
        finally:
            ordering.close()

    def test_paying_for_an_order_with_no_engine_is_a_fault(self) -> None:
        ordering = component.Ordering(component.Config(component.Spec(engine_url="http://127.0.0.1:9")))
        try:
            with pytest.raises(Exception) as excinfo:
                asyncio.run(
                    ordering.client.make_order_payment(
                        client.MakeOrderPaymentRequest(
                            order_id="o1", sku="widget", quantity=2, payment_method="card-4242"
                        )
                    )
                )
            assert not isinstance(excinfo.value, client.ERRORS)
        finally:
            ordering.close()

    def test_an_order_the_domain_refuses_is_the_situation_of_that_name(self) -> None:
        ordering = component.Ordering(component.Config(component.Spec(engine_url="http://127.0.0.1:9")))
        try:
            with pytest.raises(client.OrderRejected):
                asyncio.run(
                    ordering.client.place_order(
                        client.PlaceOrderRequest(order_id="o1", sku="widget", quantity=0)
                    )
                )
        finally:
            ordering.close()


class TestOrderingThroughTheEngine:

    async def test_each_declared_situation_reaches_the_caller_as_its_own_error(self, engine_url: str, engine_admin_url: str, engine_callback_host: str, free_port: int) -> None:
        ordering = component.Ordering(
            component.Config(component.Spec(engine_url=engine_url))
        )
        containers: list[restate.Service | restate.Workflow] = [
            ordering.order_actions_service,
            ordering.order_orchestrator_workflow,
            ordering.purchase_actions_service,
            ordering.purchase_orchestrator_workflow,
        ]
        port = free_port
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app(containers)),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=engine_admin_url, timeout=10.0)
        registered = httpx.Response(503)
        try:
            for _ in range(50):
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{engine_callback_host}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            placed = str(uuid.uuid4())
            await ordering.client.place_order(
                client.PlaceOrderRequest(order_id=placed, sku="widget", quantity=1)
            )
            with pytest.raises(client.OrderAlreadyStarted):
                await ordering.client.place_order(
                    client.PlaceOrderRequest(order_id=placed, sku="widget", quantity=1)
                )
            with pytest.raises(client.OrderNotConfirmed):
                await ordering.client.make_order_payment(
                    client.MakeOrderPaymentRequest(
                        order_id=placed, sku="widget", quantity=1, payment_method="card-4242"
                    )
                )
            with pytest.raises(client.ProductPriceNotFound):
                await ordering.client.place_order(
                    client.PlaceOrderRequest(order_id=str(uuid.uuid4()), sku="nothing", quantity=1)
                )
            with pytest.raises(client.PaymentDeclined):
                await ordering.client.make_order_payment(
                    client.MakeOrderPaymentRequest(
                        order_id=str(uuid.uuid4()),
                        sku="widget",
                        quantity=1,
                        payment_method="declined",
                    )
                )
        finally:
            if registered.is_success:
                await admin.delete(
                    f"/deployments/{registered.json()['id']}", params={"force": "true"}
                )
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
            ordering.close()
