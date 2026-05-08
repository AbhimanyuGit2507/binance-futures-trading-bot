from __future__ import annotations

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from requests.exceptions import RequestException

from bot.client import BinanceFuturesClient
from bot.exceptions import BinanceClientError, ValidationError
from bot.models import OrderResult
from bot.logging_config import configure_logging
from bot.orders import build_order_payload, format_order_result
from bot.validators import OrderInput, parse_order_input


app = typer.Typer(add_completion=False, help="Binance Futures Testnet trading bot")
console = Console()
logger = configure_logging()


@app.callback()
def main() -> None:
    return None


def _print_summary(order: OrderInput) -> None:
    table = Table(title="Order Summary", show_header=False)
    table.add_row("Symbol", order.symbol)
    table.add_row("Side", order.side)
    table.add_row("Type", order.order_type)
    table.add_row("Quantity", str(order.quantity))
    table.add_row("Price", "-" if order.price is None else str(order.price))
    table.add_row("Stop Price", "-" if order.stop_price is None else str(order.stop_price))
    console.print(table)


def _print_result(result_text: str, success: bool) -> None:
    title = "Order Placed" if success else "Order Failed"
    border = "green" if success else "red"
    console.print(Panel(result_text, title=title, border_style=border))


def _print_order_response(result: OrderResult) -> None:
    table = Table(title="Order Response", show_header=False)
    table.add_row("Status", result.status)
    table.add_row("Symbol", result.symbol)
    table.add_row("Side", result.side)
    table.add_row("Type", result.order_type)
    table.add_row("Quantity", str(result.quantity))
    table.add_row("Price", "-" if result.price is None else str(result.price))
    table.add_row("Stop Price", "-" if result.stop_price is None else str(result.stop_price))
    table.add_row("Order ID", "-" if result.order_id is None else str(result.order_id))
    table.add_row(
        "Client Order ID",
        "-" if result.client_order_id is None else result.client_order_id,
    )
    table.add_row("Created At", result.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    console.print(Panel(table, title="Order Placed", border_style="green"))


def _print_error(message: str, title: str = "Validation Error") -> None:
    console.print(Panel(message, title=title, border_style="red"))


@app.command("place-order")
def place_order(
    symbol: str = typer.Option(..., "--symbol"),
    side: str = typer.Option(..., "--side"),
    order_type: str = typer.Option(..., "--type"),
    quantity: float = typer.Option(..., "--quantity"),
    price: float | None = typer.Option(None, "--price"),
    stop_price: float | None = typer.Option(None, "--stop-price"),
) -> None:
    load_dotenv()
    try:
        order = parse_order_input(
            symbol=symbol,
            side=side.upper(),
            order_type=order_type.upper(),
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValidationError as exc:
        logger.exception("validation error")
        _print_error(str(exc))
        raise typer.Exit(code=1)

    _print_summary(order)
    logger.info("validated order %s", build_order_payload(order))

    try:
        client = BinanceFuturesClient.from_env()
        if order.order_type == "MARKET":
            response = client.place_market_order(
                symbol=order.symbol,
                side=order.side,
                quantity=str(order.quantity),
            )
        elif order.order_type == "LIMIT":
            response = client.place_limit_order(
                symbol=order.symbol,
                side=order.side,
                quantity=str(order.quantity),
                price=str(order.price),
            )
        else:
            response = client.place_stop_limit_order(
                symbol=order.symbol,
                side=order.side,
                quantity=str(order.quantity),
                price=str(order.price),
                stop_price=str(order.stop_price),
            )
    except (BinanceClientError, RequestException) as exc:
        logger.exception("order placement failed")
        _print_result(str(exc), success=False)
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.exception("unexpected order placement failure")
        _print_result(f"Unexpected error: {exc}", success=False)
        raise typer.Exit(code=1)

    result = format_order_result(order, response)
    _print_order_response(result)


if __name__ == "__main__":
    app()
