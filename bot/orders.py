from __future__ import annotations

from typing import Any

from bot.models import OrderResult
from bot.utils import to_decimal_string
from bot.validators import OrderInput


def build_order_payload(order: OrderInput) -> dict[str, str]:
    payload = {
        "symbol": order.symbol,
        "side": order.side,
        "type": order.order_type,
        "quantity": to_decimal_string(order.quantity),
    }
    if order.price is not None:
        payload["price"] = to_decimal_string(order.price)
    if order.stop_price is not None:
        payload["stop_price"] = to_decimal_string(order.stop_price)
    return payload


def format_order_result(order: OrderInput, response: dict[str, Any]) -> OrderResult:
    return OrderResult(
        status=response.get("status", "UNKNOWN"),
        symbol=order.symbol,
        side=order.side,
        order_type=order.order_type,
        quantity=order.quantity,
        price=order.price,
        stop_price=order.stop_price,
        order_id=response.get("orderId"),
        client_order_id=response.get("clientOrderId"),
        raw_response=response,
    )
