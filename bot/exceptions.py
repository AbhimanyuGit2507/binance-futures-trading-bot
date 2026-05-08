class TradingBotError(Exception):
    pass


class ValidationError(TradingBotError):
    pass


class BinanceClientError(TradingBotError):
    pass
