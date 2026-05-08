from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    side: str
    order_type: str = Field(alias="type")
    quantity: float
    price: float | None = None
    stop_price: float | None = None


class OrderResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    order_id: int | None = None
    client_order_id: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
