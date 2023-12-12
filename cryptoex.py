import requests


class Cryptoex:
    """
    A class for working with cryptoexchange data

    Attributes:
    ^^^^^^^^^^^

    :exchanges: a dict of URLs of supported exchanges for each type of processing function
    :default_dkey: default keys with which the processed exchange's response is returned
    :exchange_dkey: the keys of the exchange, with which the required data is returned

    :exception BadExchangeError: unsupported or incorrect exchange
    :exception BadTickerError: ticker not contain `-` as a separator
    :exception InitError: no match was found between the default key and the exchange key
    :exception The exchange's response does not match the format for this request

    Methods:
    ^^^^^^^^

    """
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
                "ticker_stream": ['last', 'changeRate'],
                "exchange_stream": ["last", "changeRate"]},
        "BitMart":
            {
                "ticker_stream": ["last", "fluctuation"],
                "exchange_stream": [1, 7]}
    }

    class BadExchangeError(Exception): pass
    class BadTickerError(Exception): pass
    class InitError(Exception): pass
    class BadResponseError(Exception): pass

    def __init__(self):
        """
            Function checks whether the default key matches all the keys of the exchange.

            :raise InitError: If it is impossible to establish a match, the InitError will be thrown
            :rtype: none
        """
        for exchange in self.exchange_dkey:
            for dkey in self.exchange_dkey[exchange]:
                keys = self.exchange_dkey[exchange][dkey]
                if len(keys) < len(self.default_dkey):
                    diff = len(self.default_dkey)-len(keys)
                    raise self.InitError(f"Error: {exchange} {dkey} must be supplemented with {diff} keys")

    def klines(self, ticker, interval, limit):
        """Function of sending data for plotting

        The function makes a request to the exchange and allocates from it the start and end times,
        and the cost of the ticker at each time multiple of the interval.
        If the request fails, the BadResponseError will be thrown.
        The data for plotting the ticker is provided by the exchange Binance

        :param ticker: the ticker for which you need to build a graph
        :param interval: The step with which you need to receive the cost (e.g. 1h, 1d, 1w)
        :param limit: the number of steps from the present time with defined interval back
        :return: exchange name, ticker, start and end time, interval, array of ticker values at each step
        :rtype: dict

        """
        exchange = 'Binance'
        ticker = ticker.replace("-", self.exchanges[exchange]["ticker_sep"])
        try:
            params = f"symbol={ticker}&interval={interval}&limit={limit}"
            response = requests.get(f'{self.exchanges[exchange]["kline_stream"]}?{params}').json()
            from_t, to_t = int(response[0][0]) / 1000, int(response[-1][0]) / 1000
        except Exception:
            raise self.BadResponseError("Error: exchange response isn't JSON. Check your request")
        conv_interval = {"1d": 86400}
        result = {'exchange': exchange, 'ticker': ticker, 'from': from_t, 'to': to_t,
                  'interval': conv_interval[interval], 'close_price': [x[4] for x in response]}
        return result

    def exchange_data(self, exchange):  # get all exchange tickers
        """
        Function to get the data of all tickers of a defined exchange

        :raise BadExchangeError: the exchange is not supported
        :raise BadResponseError: the exchange's response is not correct or has an error code
        :param exchange: one of the supported exchanges
        :return: A list containing the name of the ticker, the cost and its change in 24 hours
        :rtype: list

        """
        if exchange not in self.exchanges:  # exchange is not supported
            raise self.BadExchangeError(f"Error: unsupported or incorrect exchange {exchange}")
        result = list()    # value to return
        try:
            response = requests.get(self.exchanges[exchange]["exchange_stream"]).json()
        except Exception:
            raise self.BadResponseError("Error: exchange response isn't JSON. Check your request")
        result_key = {"BitMart": ['data'], "Bybit": ['result', 'list'], "Binance": [], "KuCoin": ['data', 'ticker']}
        for i in range(len(result_key[exchange])):
            response = response[result_key[exchange][i]]    # extracting useful data from the exchange's response
        for exchange_ticker in response:    # for every ticker
            tp_key = {"BitMart": 0, "Bybit": 's', "Binance": "symbol", "KuCoin": "symbol"}  # ticker symbol key
            r = {"Exchange": exchange, "Trade pair": exchange_ticker[tp_key[exchange]]}    # form result
            for i in range(len(self.default_dkey)):    # mapping of default keys to the keys used by the exchange
                exchange_dkey = self.exchange_dkey[exchange]["exchange_stream"][i]
                default_dkey = self.default_dkey[i]
                if exchange_dkey is None:   # if the key mapping isn't defined by exchange
                    r[default_dkey] = ""
                    continue
                r[default_dkey] = exchange_ticker[exchange_dkey]    # saving the exchange value with the default key
                if default_dkey == "Fluctuation":   # convert the price change into a percentage
                    if exchange != "Binance":
                        r[default_dkey] = str(round(float(r[default_dkey]) * 100, 2))
                    r[default_dkey] += "%"
            result.append(r)
        return result

    def ticker_data(self, ticker, exchange):
        """
        Function to get the data of defined ticker of defined exchange

        :raise BadTickerError: The ticker must contain `-` as a separator
        :raise BadResponseError: the exchange's response is not correct or has an error code
        :param ticker: the name of the ticker(e.g. BTC-USDT, ETH-USDT)
        :param exchange: one of the supported exchanges
        :return: A list containing the name of the exchange, ticker, the cost and its change in 24 hours
        :rtype: list
        """
        if "-" not in ticker:
            raise self.BadTickerError("ticker must contain `-` as a separator")
        ticker = ticker.replace('-', self.exchanges[exchange]['ticker_sep'])
        try:
            params = f"symbol={ticker}"
            response = requests.get(f"{self.exchanges[exchange]['ticker_stream']}?{params}").json()
        except Exception:
            raise self.BadResponseError("Error: exchange response isn't JSON. Check your request")
        result_key = {"BitMart": ['data'], "Bybit": ['result'], "Binance": [], "KuCoin": ['data']}
        for i in range(len(result_key[exchange])):
            response = response[result_key[exchange][i]]  # extracting the data from the exchange's response
        result = {"Exchange": exchange, "Trade pair": ticker}
        for i in range(len(self.default_dkey)):    # mapping of default keys to the keys used by the exchange
            exchange_dkey = self.exchange_dkey[exchange]["ticker_stream"][i]
            default_dkey = self.default_dkey[i]
            if exchange_dkey is None:                                       # if the key mapping is not defined
                result[default_dkey] = ""
                continue
            result[default_dkey] = response[exchange_dkey]
            if default_dkey == "Fluctuation":     # convert the price change into a percentage
                if exchange != "Binance":
                    result[default_dkey] = str(round(float(result[default_dkey]) * 100, 2))
                result[default_dkey] += "%"
        return result


# c = Cryptoex()
# print(c.klines("BTCUSDT","1d","3"))