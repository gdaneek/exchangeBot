import requests
from datetime import datetime, timedelta


class MoexExchange:
    """
    A class for working with MOEX data
    """

    def __init__(self):
        """
         Function checks whether the default key matches all the keys of the exchange.
        :rtype: None
        :raise InitError: If it is impossible to establish a match, the InitError will be thrown
        """
        self.base_url = "https://api.moex.com"

    def make_request(self, url):
        """
        Function, that makes GET-request for API of MOEX stock market and returns json-answer

        :param: url: completed url for MOEX request
        :type url: str
        :return: dict with MOEX reply with P/E, current price, MarketCap multiplicators
        :rtype: dict
        :raise: requests.exceptions.RequestException: In case of incorrect request or empty answer.
        """

        response = requests.get(url)
        response.raise_for_status()
        return response.json()


    def ticker_data(self, ticker):
        """
        Function, that returns information about ticker: P/E, Current price, MarketCap

        :param ticker: letter short name of financial active(cryptocoin or stock)
        :type ticker: str
        :return:
        :rtype:
        Returns:
            tuple: Кортеж с значениями P/E, текущей цены и MarketCap.

        :raise: ValueError: In case of not-found ticker.
        """
        url = f"{self.base_url}/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker.upper()}.json"


        data = self.make_request(url)
        if "marketdata" in data:
            pe_ratio = data["marketdata"]["pe_ratio"]
            current_price = data["marketdata"]["capitalization"]
            market_cap = data["marketdata"]["market_cap"]
            return pe_ratio, current_price, market_cap
        else:
            raise ValueError("Ticker not found.")

    def exchange_data(self): pass
    def klines(self, ticker):
        """
        Сохраняет график изменения цены тикера за последний год на устройство.

        Args:
            ticker (str): Тикер акции или инструмента.
        """
        url = f"{self.base_url}/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker.upper()}.json"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        data = self.make_request(url)
        if "history" in data:
            prices = []
            dates = []
            for item in data["history"]["data"]:
                date = datetime.strptime(item[1], "%Y-%m-%d")
                if start_date <= date <= end_date:
                    prices.append(item[7])
                    dates.append(date)

        else:
            raise ValueError("Ticker not found.")
