class Cryptoex:

    exchanges = {
        'Binance': {
            "ticker_stream": "https://api.binance.com/api/v3/ticker/24hr",
            "exchange_stream": "https://api.binance.com/api/v3/ticker/24hr",
            "kline_stream": "https://api.binance.com/api/v3/klines",
            "ticker_sep": ""},
        'Bybit': {
            "ticker_stream": "https://api.bybit.com/spot/v3/public/quote/ticker/24hr",
            "exchange_stream": "https://api.bybit.com/spot/v3/public/quote/ticker/24hr",
            "ticker_sep": ""},
        'KuCoin': {
            "ticker_stream": "https://api.kucoin.com/api/v1/market/stats",
            "exchange_stream": "https://api.kucoin.com/api/v1/market/allTickers",
            "ticker_sep": "-"},
        'BitMart': {
            "ticker_stream": "https://api-cloud.bitmart.com/spot/quotation/v3/ticker",
            "exchange_stream": "https://api-cloud.bitmart.com/spot/quotation/v3/tickers",
            "ticker_sep": "_"}
    }
    default_dkey = ["Price", "Fluctuation"]
    exchange_dkey = {
        "Binance":
            {"exchange_stream": ["lastPrice", "priceChangePercent"]},
        "Bybit":
            {"exchange_stream": ['lp', None]},
        "KuCoin":
            {"exchange_stream": ["last", "changeRate"]},
        "BitMart":
            {"exchange_stream": [1, 7]}
    }

    def __init__(self):
        pass

    def klines(self, exchange, ticker, interval='1d', lim=365):
        pass

    def exchange_data(self, exchange):  # get all exchange tickers
        pass

