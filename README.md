# Binance Futures Testnet Trading Bot

Small, focused Python CLI for placing MARKET, LIMIT, and STOP_LIMIT orders on Binance Futures Testnet (USDT‑M). This repository contains a minimal but realistic engineering implementation with validation, logging, retries, and a clean CLI.

## Features

- BUY and SELL orders
- MARKET, LIMIT, and STOP_LIMIT order types
- Pydantic (v2) input validation with helpful error messages
- Rich-formatted CLI output for summaries and order responses
- Rotating file logging with request/response payloads, timestamps, and version tags
- Tenacity retry logic for transient network failures
- Symbol precision validation against Binance exchange filters

## Architecture

- `bot/client.py` — Binance Futures wrapper (testnet) with `place_market_order`, `place_limit_order`, and `place_stop_limit_order`.
- `bot/validators.py` — Pydantic models and input parsing.
- `bot/orders.py` — small helpers to build request payloads and format responses.
- `cli.py` — Typer-based CLI entrypoint.
- `bot/logging_config.py` — Rotating file logger to `logs/trading_bot.log`.

## Setup

Create and activate a Python virtualenv, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root with your Binance Futures Testnet keys (DO NOT commit this file):

```text
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
```

## Environment Variables

- `BINANCE_API_KEY` — Testnet API key
- `BINANCE_API_SECRET` — Testnet secret

## Usage

Example commands:

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
python cli.py place-order --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 70500 --stop-price 71000
```

The CLI will print a brief order summary, then an order response table. Failures are shown with a red panel and the details are written to `logs/trading_bot.log`.

## Example Output

- See `sample_outputs/market_order.txt` and `sample_outputs/limit_order.txt` for captured terminal output from actual testnet orders.
- See `sample_outputs/sample_log.txt` for the corresponding log entries (request and response payloads and timestamps).

## Logging

All request and response payloads (non-sensitive) are logged to `logs/trading_bot.log` with timestamps, version tags, and level. The logger is file-only to keep the CLI output clean. Example entries are preserved in `sample_outputs/sample_log.txt`.

## Error Handling

- Input validation errors: surfaced to user via CLI panel and logged.
- Binance API errors: captured, formatted, and logged with context. Example: `APIError(code=-4024): Limit price can't be lower than X`.
- Transient network errors: retried up to 3 times with exponential backoff via Tenacity.
- Symbol precision errors: detected before request submission using Binance exchange filters.

## Assumptions

- This project targets Binance Futures Testnet (USDT‑M) only.
- No position management or trade strategies are implemented.
