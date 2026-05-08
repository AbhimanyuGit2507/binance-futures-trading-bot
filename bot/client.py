from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from bot.exceptions import BinanceClientError, ValidationError
from bot.logging_config import configure_logging
from bot.utils import format_binance_api_error, is_multiple_of_step


@dataclass(slots=True)
class BinanceFuturesClient:
    api_key: str
    api_secret: str
    logger: Any = None
    client: Any = None
    exchange_info: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        load_dotenv()
        self.logger = configure_logging()
        if not self.api_key or not self.api_secret:
            raise BinanceClientError("missing BINANCE_API_KEY or BINANCE_API_SECRET")

        self.client = Client(self.api_key, self.api_secret, testnet=True)

    @classmethod
    def from_env(cls) -> "BinanceFuturesClient":
        return cls(
            api_key=os.getenv("BINANCE_API_KEY", "").strip(),
            api_secret=os.getenv("BINANCE_API_SECRET", "").strip(),
        )

    def _log_request(self, endpoint: str, payload: dict[str, Any]) -> None:
        self.logger.info("request %s %s", endpoint, payload)

    def _log_response(self, endpoint: str, payload: dict[str, Any]) -> None:
        self.logger.info("response %s %s", endpoint, payload)

    def _raise_client_error(self, error: Exception) -> BinanceClientError:
        formatted = format_binance_api_error(error)
        self.logger.exception(formatted)
        return BinanceClientError(formatted)

    def _get_exchange_info(self) -> dict[str, Any]:
        if self.exchange_info is None:
            self.exchange_info = self.client.futures_exchange_info()
        return self.exchange_info

    def _get_symbol_info(self, symbol: str) -> dict[str, Any]:
        exchange_info = self._get_exchange_info()
        for item in exchange_info.get("symbols", []):
            if item.get("symbol") == symbol:
                return item
        raise BinanceClientError(f"symbol {symbol} not found in exchange info")

    def _get_filter(self, symbol_info: dict[str, Any], filter_type: str) -> dict[str, Any]:
        for filter_item in symbol_info.get("filters", []):
            if filter_item.get("filterType") == filter_type:
                return filter_item
        raise BinanceClientError(f"filter {filter_type} not found for symbol {symbol_info.get('symbol')}")

    def validate_order_precision(
        self,
        *,
        symbol: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
        stop_price: str | None = None,
    ) -> None:
        symbol_info = self._get_symbol_info(symbol)
        quantity_filters = ["MARKET_LOT_SIZE", "LOT_SIZE"] if order_type == "MARKET" else ["LOT_SIZE", "MARKET_LOT_SIZE"]

        quantity_filter = None
        for filter_type in quantity_filters:
            try:
                quantity_filter = self._get_filter(symbol_info, filter_type)
                break
            except BinanceClientError:
                continue

        if quantity_filter is None:
            raise BinanceClientError(f"quantity filter not found for symbol {symbol}")

        step_size = quantity_filter.get("stepSize")
        if step_size is not None and not is_multiple_of_step(quantity, step_size):
            raise ValidationError(
                f"quantity {quantity} does not match step size {step_size} for {symbol}"
            )

        if order_type in {"LIMIT", "STOP_LIMIT"}:
            price_filter = self._get_filter(symbol_info, "PRICE_FILTER")
            tick_size = price_filter.get("tickSize")

            if price is not None and tick_size is not None and not is_multiple_of_step(price, tick_size):
                raise ValidationError(
                    f"price {price} does not match tick size {tick_size} for {symbol}"
                )

            if stop_price is not None and tick_size is not None and not is_multiple_of_step(stop_price, tick_size):
                raise ValidationError(
                    f"stop_price {stop_price} does not match tick size {tick_size} for {symbol}"
                )

    @retry(
        retry=retry_if_exception_type((RequestException, ConnectionError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def place_market_order(self, *, symbol: str, side: str, quantity: str) -> dict[str, Any]:
        self.validate_order_precision(symbol=symbol, order_type="MARKET", quantity=quantity)
        payload = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
        self._log_request("place_market_order", payload)
        try:
            response = self.client.futures_create_order(**payload)
        except (BinanceAPIException, BinanceOrderException) as exc:
            raise self._raise_client_error(exc)
        self._log_response("place_market_order", response)
        return response

    @retry(
        retry=retry_if_exception_type((RequestException, ConnectionError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def place_limit_order(self, *, symbol: str, side: str, quantity: str, price: str) -> dict[str, Any]:
        self.validate_order_precision(
            symbol=symbol,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
        )
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price,
        }
        self._log_request("place_limit_order", payload)
        try:
            response = self.client.futures_create_order(**payload)
        except (BinanceAPIException, BinanceOrderException) as exc:
            raise self._raise_client_error(exc)
        self._log_response("place_limit_order", response)
        return response

    @retry(
        retry=retry_if_exception_type((RequestException, ConnectionError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def place_stop_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        stop_price: str,
    ) -> dict[str, Any]:
        self.validate_order_precision(
            symbol=symbol,
            order_type="STOP_LIMIT",
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
        }
        self._log_request("place_stop_limit_order", payload)
        try:
            response = self.client.futures_create_order(**payload)
        except (BinanceAPIException, BinanceOrderException) as exc:
            raise self._raise_client_error(exc)
        self._log_response("place_stop_limit_order", response)
        return response
