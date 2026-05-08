from __future__ import annotations

import unittest

from bot.exceptions import ValidationError
from bot.utils import decimal_places, format_binance_api_error, is_multiple_of_step
from bot.validators import parse_order_input


class DummyBinanceError(Exception):
    def __init__(self, message: str, *, code: int | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ValidatorTests(unittest.TestCase):
    def test_invalid_side_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            parse_order_input(
                symbol="BTCUSDT",
                side="HOLD",
                order_type="MARKET",
                quantity=0.001,
            )

    def test_negative_quantity_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            parse_order_input(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=-0.001,
            )

    def test_limit_order_without_price_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            parse_order_input(
                symbol="BTCUSDT",
                side="SELL",
                order_type="LIMIT",
                quantity=0.001,
            )


class UtilityTests(unittest.TestCase):
    def test_step_size_check(self) -> None:
        self.assertTrue(is_multiple_of_step("0.001", "0.001"))
        self.assertFalse(is_multiple_of_step("0.0015", "0.001"))

    def test_decimal_places(self) -> None:
        self.assertEqual(decimal_places("0.0100"), 2)

    def test_binance_error_formatter(self) -> None:
        error = DummyBinanceError("Invalid API-key", code=-2015, status_code=401)
        message = format_binance_api_error(error)
        self.assertIn("Binance API Error", message)
        self.assertIn("code=-2015", message)
        self.assertIn("status=401", message)
        self.assertIn("Invalid API-key", message)


if __name__ == "__main__":
    unittest.main()