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
            {"exchange_stream": ["lastPrice", "priceChangePercent"]},
        "Bybit":
            {"exchange_stream": ['lp', None]},
        "KuCoin":
            {"exchange_stream": ["last", "changeRate"]},
        "BitMart":
            {"exchange_stream": [1, 7]}
    }

    def __init__(self):
        for exchange in self.exchange_dkey:
            for dkey in self.exchange_dkey[exchange]:
                keys = self.exchange_dkey[exchange][dkey]
                if len(keys) < len(self.default_dkey):
                    print(f"{exchange} {dkey} must be supplemented with {len(self.default_dkey) - len(keys)} keys")
                    self.exchange_dkey[exchange][dkey].extend([None] * (len(self.default_dkey) - len(keys)))

    def klines(self, exchange, ticker, interval='1d', lim=365):
        ticker = ticker.replace("-", self.exchanges[exchange]["ticker_sep"])
        response = requests.get(
            f'{self.exchanges[exchange]["kline_stream"]}?symbol={ticker}&interval={interval}&limit={lim}').json()
        from_t, to_t = int(response[0][0]) / 1000, int(response[-1][0]) / 1000
        conv_interval = {"1d": 86400}
        close_price = [x[4] for x in response]
        result = {'exchange': exchange, 'ticker': ticker, 'from': from_t, 'to': to_t,
                  'interval': conv_interval[interval], 'close_price': close_price}
        return result

    def exchange_data(self, exchange):  # get all exchange tickers
        if exchange not in self.exchanges:  # exchange is not supported
            return f"Error: unsupported or incorrect exchange {exchange}", 404
        result = list()  # value to return
        response = requests.get(self.exchanges[exchange]["exchange_stream"])  # the exchange's response to the request
        status_code = response.status_code  # response code (e.g. 200,404)
        response = response.json()  # convert to json format
        result_key = {"BitMart": ['data'], "Bybit": ['result', 'list'], "Binance": [], "KuCoin": ['data', 'ticker']}
        for i in range(len(result_key[exchange])):
            response = response[result_key[exchange][i]]  # extracting the data from the exchange's response
        for exchange_ticker in response:  # for every ticker
            tp_key = {"BitMart": 0, "Bybit": 's', "Binance": "symbol", "KuCoin": "symbol"}  # ticker symbol key
            r = {"Exchange": exchange, "Trade pair": exchange_ticker[tp_key[exchange]]}  # intermediate result
            for i in range(len(self.default_dkey)):  # mapping of default keys to the keys used by the exchange
                exchange_dkey = self.exchange_dkey[exchange]["exchange_stream"][i]  # dkey means data key
                default_dkey = self.default_dkey[i]
                if exchange_dkey is None:  # if the key mapping is not defined
                    r[default_dkey] = ""
                    continue
                r[default_dkey] = exchange_ticker[exchange_dkey]  # saving the exchange value with the default key
                if default_dkey == "Fluctuation":  # convert the price change into a percentage
                    r[default_dkey] = str(round(float(r[default_dkey]) * 100, 2)) + "%"
            result.append(r)  # adding intermediate data to the result
        return result, status_code
    
    def ticker_data(self):
        pass
