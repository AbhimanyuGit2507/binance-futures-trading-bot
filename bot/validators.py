from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, field_validator, model_validator

from bot.exceptions import ValidationError


SymbolValue = str
OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "STOP_LIMIT"]


class OrderInput(BaseModel):
    symbol: SymbolValue = Field(min_length=3, max_length=20)
    side: OrderSide
    order_type: OrderType
    quantity: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{3,20}", cleaned):
            raise ValueError("symbol must contain only uppercase letters and numbers")
        return cleaned

    @model_validator(mode="after")
    def validate_prices(self) -> "OrderInput":
        if self.order_type == "LIMIT" and self.price is None:
            raise ValueError("price is required for LIMIT orders")
        if self.order_type == "STOP_LIMIT" and self.price is None:
            raise ValueError("price is required for STOP_LIMIT orders")
        if self.order_type == "STOP_LIMIT" and self.stop_price is None:
            raise ValueError("stop_price is required for STOP_LIMIT orders")
        if self.order_type == "MARKET" and self.price is not None:
            raise ValueError("price should not be provided for MARKET orders")
        return self


def parse_order_input(**data: object) -> OrderInput:
    try:
        return OrderInput(**data)
    except (PydanticValidationError, ValueError) as exc:
        raise ValidationError(str(exc)) from exc
