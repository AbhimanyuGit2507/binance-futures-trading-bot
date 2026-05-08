from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_VERSION = "0.2.0"


def configure_logging(version: str = APP_VERSION) -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(f"%(asctime)s | v{version} | %(levelname)s | %(message)s")

    file_handler = RotatingFileHandler(
        log_dir / "trading_bot.log",
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.info("logging initialized version=%s", version)
    return logger
