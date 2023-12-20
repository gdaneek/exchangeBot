import json
import requests


class MoexExchange:
    """
    A class for working with MOEX data
    """

    base_url = ""
    """
    the URL of the exchange
    """

    class BadExchangeResponse(Exception):
        """
        triggered if the server response does not contain the required fields
        """
        pass

    def __init__(self):
        """
         Function checks whether the default key matches all the keys of the exchange.
         :return: -
        :rtype: None
        """
        self.base_url = "https://iss.moex.com"

    def make_request(self, url):
        """
        Function, that makes GET-request for API of MOEX stock market and returns json-answer

        :param: url: completed url for MOEX request
        :type url: str
        :return: dict with MOEX reply with P/E, current price, MarketCap multiplicators
        :rtype: dict
        """
        response = requests.get(url)
        return response.json()

    def ticker_data(self, ticker, **kwargs):
        """
        Function, that returns information about ticker: P/E, Current price, MarketCap

        :param ticker: letter short name of financial active(cryptocoin or stock)
        :type ticker: str
        :return: information about the ticker, including P/E, market price and market cap
        :rtype: dict
        :raise: BadExchangeResponse: In case of not-found ticker.
        """
        url = f"{self.base_url}/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker.upper()}.json"
        data = self.make_request(url)
        print(data)
        # 0 - SBER , P/E - , market price - 25-1, volume 28-1
        if "marketdata" in data:
            ticker = data["marketdata"]['data'][0][0]
            current_price = data["marketdata"]["data"][0][24]
            market_cap = data["marketdata"]["data"][0][27]
            pe = data["marketdata"]["data"][0][21]
            result = {
                "Ticker": f"{ticker}",
                "Current price": f"{current_price} RUB",
                "Market cap": f"{market_cap} RUB",
                "P/E":  f"{pe}"
            }
            return result
        else:
            raise self.BadExchangeResponse("Data not found")

    def exchange_data(self, **kwargs):
        """
        a function that returns information about all stock exchange tickers
        :return: a list of dictionaries with information for each ticker
        :type: list
        """
        response = self.make_request(f"{self.base_url}/iss/engines/stock/markets/shares/boards/TQBR/securities.json")

        # with open("moex_ex_data_in.json", 'w') as f:
        #     f.write(json.dumps(response))
        result = []
        if "marketdata" in response:
            data = response["marketdata"]['data']
        else:
            raise self.BadExchangeResponse("Data not found")
        for i in range(len(data)):
            ticker = data[i][0]
            current_price = data[i][24]
            market_cap = data[i][27]
            pe = data[i][21]
            r = {
                "Ticker": f"{ticker}",
                "Current price": f"{current_price} RUB",
                "Market cap": f"{market_cap} RUB",
                "P/E":  f"{pe}"
                }
            result.append(r)

        return result

    def klines(self):
        """
            a stub function that copies the name of a similar function from cryptoex so that errors do not occur
        """
        pass

# m = MoexExchange()
# with open("moex_ex_data_out.json", 'w') as f:
#     f.write(json.dumps(m.exchange_data()))

