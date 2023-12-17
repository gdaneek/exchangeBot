import pytest
from unittest.mock import Mock
import requests
from cryptoex import Cryptoex
import json
data_IO = json.loads(open("tests_data_IO.json").read())
cryptoex = Cryptoex()

# ------------------------  exchange_data testing ------------------------ #


def test_exchange_data_unsupported_exchange():
    with pytest.raises(cryptoex.BadExchangeError):
        exchange = "bInance"
        cryptoex.exchange_data(exchange)


def test_exchange_data_wrong_parameter_type():
    with pytest.raises(cryptoex.BadExchangeError):
        exchange = 1.25
        cryptoex.exchange_data(exchange)


def test_exchange_data_bad_exchange_response():
    with pytest.raises(cryptoex.BadResponseError):
        exchange = "Binance"
        requests.get = Mock()
        requests.get.return_value = "{}"
        cryptoex.exchange_data(exchange)


def test_exchange_data_successful_binance():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_exchange_data_successful_binance_input"]
    assert cryptoex.exchange_data("Binance") == data_IO["test_exchange_data_successful_binance_output"]


def test_exchange_data_successful_bybit():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_exchange_data_successful_bybit_input"]
    assert cryptoex.exchange_data("Bybit") == data_IO["test_exchange_data_successful_bybit_output"]


def test_exchange_data_successful_bitmart():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_exchange_data_successful_bitmart_input"]
    assert cryptoex.exchange_data("BitMart") == data_IO["test_exchange_data_successful_bitmart_output"]


def test_exchange_data_successful_kucoin():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_exchange_data_successful_kucoin_input"]
    assert cryptoex.exchange_data("KuCoin") == data_IO["test_exchange_data_successful_kucoin_output"]


# ------------------------  exchange_data testing ------------------------ #


def test_ticker_data_bad_ticker():
    with pytest.raises(cryptoex.BadTickerError):
        ticker = "BTCUSDT"
        cryptoex.ticker_data(ticker, "Binance")


def test_ticker_data_bad_ticker_type():
    with pytest.raises(cryptoex.BadTickerError):
        ticker = 12345
        cryptoex.ticker_data(ticker, "Binance")


def test_ticker_data_bad_response():
    with pytest.raises(cryptoex.BadResponseError):
        ticker = "btc-usdt"
        requests.get = Mock()
        requests.get.return_value = "{}"
        cryptoex.ticker_data(ticker, "Binance")


def test_ticker_data_successful_binance():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_ticker_data_successful_binance_input"]
    assert cryptoex.ticker_data("BTC-USDT", "Binance") == data_IO["test_ticker_data_successful_binance_output"]


def test_ticker_data_successful_bybit():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_ticker_data_successful_bybit_input"]
    assert cryptoex.ticker_data("BTC-USDT", "Bybit") == data_IO["test_ticker_data_successful_bybit_output"]


def test_ticker_data_successful_kucoin():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_ticker_data_successful_kucoin_input"]
    assert cryptoex.ticker_data("BTC-USDT", "KuCoin") == data_IO["test_ticker_data_successful_kucoin_output"]


def test_ticker_data_successful_bitmart():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_ticker_data_successful_bitmart_input"]
    assert cryptoex.ticker_data("BTC-USDT", "BitMart") == data_IO["test_ticker_data_successful_bitmart_output"]

# --------------------------------------    klines testing  -------------------------------------- #


def test_klines_bad_ticker():
    with pytest.raises(cryptoex.BadResponseError):
        ticker = "QWERTY"
        requests.get = Mock()
        requests.get.return_value = "{}"
        cryptoex.klines(ticker, "1d", "1")


def test_klines_bad_interval():
    with pytest.raises(cryptoex.BadResponseError):
        interval = 12.5     # interval must be '1d', '1w' or '1m' string
        requests.get = Mock()
        requests.get.return_value = "{}"
        cryptoex.klines("BTCUSDT", interval, "1")


def test_klines_bad_limit():
    with pytest.raises(cryptoex.BadResponseError):
        limit = "-1"
        requests.get = Mock()
        requests.get.return_value = "{}"
        cryptoex.klines("BTCUSDT", "1d", limit)


def test_klines_successful():
    requests.get, requests.models.Response.json = Mock(), Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json.return_value = data_IO["test_klines_successful_input"]
    assert cryptoex.klines("BTCUSDT", "1d", "3") == data_IO["test_klines_successful_output"]

# ------------------------  init testing ------------------------ #


def test_init_error():
    with pytest.raises(cryptoex.InitError):
        Cryptoex.default_dkey.append('')
        t = Cryptoex()
