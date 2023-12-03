import requests


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
            {
                "ticker_stream": ["lastPrice", "priceChangePercent"],
                "exchange_stream": ["lastPrice", "priceChangePercent"]},
        "Bybit":
            {
                "ticker_stream": ['lp', None],
                "exchange_stream": ['lp', None]},
        "KuCoin":
            {
                "ticker_stream": ['last','changeRate'],
                "exchange_stream": ["last", "changeRate"]},
        "BitMart":
            {
                "ticker_stream": ["last", "fluctuation"],
                "exchange_stream": [1, 7]}
    }

    class BadExchangeError(Exception): pass
    class BadTickerError(Exception): pass
    class InitError(Exception): pass

    class BadRequestError(Exception): pass

    def __init__(self):
        for exchange in self.exchange_dkey:
            for dkey in self.exchange_dkey[exchange]:
                keys = self.exchange_dkey[exchange][dkey]
                if len(keys) < len(self.default_dkey):
                    #print(f"{exchange} {dkey} must be supplemented with {len(self.default_dkey)-len(keys)} keys")
                    raise self.InitError(f"Error: {exchange} {dkey} must be supplemented with {len(self.default_dkey)-len(keys)} keys")
                    #self.exchange_dkey[exchange][dkey].extend([None]*(len(self.default_dkey)-len(keys)))

    def klines(self, exchange, ticker, interval, limit):
        ticker = ticker.replace("-", self.exchanges[exchange]["ticker_sep"])
        try:
            response = requests.get(f'{self.exchanges[exchange]["kline_stream"]}?symbol={ticker}&interval={interval}&limit={limit}').json()
        except Exception:
            raise self.BadRequestError("Error: exchange response isn't JSON string. Check your request")
        from_t, to_t = int(response[0][0])/1000, int(response[-1][0])/1000
        conv_interval = {"1d": 86400}
        close_price = [x[4] for x in response]
        result = {'exchange': exchange, 'ticker': ticker, 'from': from_t, 'to': to_t,
                  'interval': conv_interval[interval], 'close_price': close_price}
        return result

    def exchange_data(self, exchange):  # get all exchange tickers
        if exchange not in self.exchanges:  # exchange is not supported
            raise self.BadExchangeError(f"Error: unsupported or incorrect exchange {exchange}")
        result = list()    # value to return
        try:
            response = requests.get(self.exchanges[exchange]["exchange_stream"]).json()    # the exchange's response to the request
        except Exception:
            raise self.BadRequestError("Error: exchange response isn't JSON string. Check your request")
        result_key = {"BitMart": ['data'], "Bybit": ['result', 'list'], "Binance": [], "KuCoin": ['data', 'ticker']}
        for i in range(len(result_key[exchange])):
            response = response[result_key[exchange][i]]    # extracting the data from the exchange's response
        for exchange_ticker in response:    # for every ticker
            tp_key = {"BitMart": 0, "Bybit": 's', "Binance": "symbol", "KuCoin": "symbol"}  # ticker symbol key
            r = {"Exchange": exchange, "Trade pair": exchange_ticker[tp_key[exchange]]}    # intermediate result
            for i in range(len(self.default_dkey)):    # mapping of default keys to the keys used by the exchange
                exchange_dkey = self.exchange_dkey[exchange]["exchange_stream"][i]  # dkey means data key
                default_dkey = self.default_dkey[i]
                if exchange_dkey is None:   # if the key mapping is not defined
                    r[default_dkey] = ""
                    continue
                r[default_dkey] = exchange_ticker[exchange_dkey]    # saving the exchange value with the default key
                if default_dkey == "Fluctuation":   # convert the price change into a percentage
                    r[default_dkey] = str(round(float(r[default_dkey]) * 100, 2)) + "%"
            result.append(r)    # adding intermediate data to the result
        return result

    def ticker_data(self, ticker, exchange):
        # key Error на exchange
        if "-" not in ticker:
            raise self.BadTickerError("ticker must contain `-` as a separator")
        ticker = ticker.replace('-', self.exchanges[exchange]['ticker_sep'])
        try:
            response = requests.get(f"{self.exchanges[exchange]['ticker_stream']}?symbol={ticker}").json()
        except Exception:
            raise self.BadRequestError("Error: exchange response isn't JSON string. Check your request")
        result_key = {"BitMart": ['data'], "Bybit": ['result'], "Binance": [], "KuCoin": ['data']}
        for i in range(len(result_key[exchange])):
            response = response[result_key[exchange][i]]  # extracting the data from the exchange's response
        result = {"Exchange": exchange, "Trade pair": ticker}
        for i in range(len(self.default_dkey)):    # mapping of default keys to the keys used by the exchange
            exchange_dkey = self.exchange_dkey[exchange]["ticker_stream"][i]  # dkey means data key
            default_dkey = self.default_dkey[i]
            if exchange_dkey is None:   # if the key mapping is not defined
                result[default_dkey] = ""
                continue
            result[default_dkey] = response[exchange_dkey]    # saving the exchange value with the default key
            if default_dkey == "Fluctuation" and exchange != "Binance":   # convert the price change into a percentage
                result[default_dkey] = str(round(float(result[default_dkey]) * 100, 2)) + "%"
        return result
