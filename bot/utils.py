from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def to_decimal_string(value: float | str | int) -> str:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric value: {value}") from exc
    return format(decimal_value.normalize(), "f")


def is_multiple_of_step(value: float | str | int, step_size: float | str | int) -> bool:
    try:
        decimal_value = Decimal(str(value))
        decimal_step = Decimal(str(step_size))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric value: {value} or step size: {step_size}") from exc

    if decimal_step <= 0:
        raise ValueError(f"step size must be greater than zero: {step_size}")

    return decimal_value % decimal_step == 0


def decimal_places(step_size: float | str | int) -> int:
    try:
        decimal_step = Decimal(str(step_size))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid step size: {step_size}") from exc

    if decimal_step <= 0:
        raise ValueError(f"step size must be greater than zero: {step_size}")

    normalized = decimal_step.normalize()
    return max(0, -normalized.as_tuple().exponent)


def format_binance_api_error(error: Exception) -> str:
    code = getattr(error, "code", None)
    message = getattr(error, "message", None) or str(error)
    status_code = getattr(error, "status_code", None)
    error_name = error.__class__.__name__

    parts: list[str] = [f"Binance API Error ({error_name})"]
    if status_code is not None:
        parts.append(f"status={status_code}")
    if code is not None:
        parts.append(f"code={code}")
    parts.append(f"message={message}")
    return " | ".join(parts)
