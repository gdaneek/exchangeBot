import pytest
from unittest.mock import Mock
import requests
from moex_exchange import MoexExchange
import json
data_IO = json.loads(open("tests_data_IO.json").read())
moex = MoexExchange()


def test_init():
    assert moex.base_url == "https://iss.moex.com"


def test_make_request():
    requests.get = Mock()
    requests.get.return_value = requests.models.Response()
    requests.models.Response.json = Mock()
    test_response = json.dumps({'a': 1})
    requests.models.Response.json.return_value = json.loads(test_response)
    test_url = "url"
    response = moex.make_request(test_url)

    requests.get.assert_called_with("url")
    assert response == {'a': 1}


def test_ticker_data():
    moex.make_request = Mock()
    moex.make_request.return_value = data_IO["moex_test_ticker_data_successful_input"]
    assert moex.ticker_data("SBER") == data_IO["moex_test_ticker_data_successful_output"]


def test_ticker_data_exc():
    with pytest.raises(moex.BadExchangeResponse):
        moex.make_request = Mock()
        moex.make_request.return_value = {}
        moex.ticker_data("SBER")


def test_exchange_data():
    moex.make_request = Mock()
    moex.make_request.return_value = json.loads(open("moex_ex_data_in.json", 'r').read())
    assert moex.exchange_data() == json.loads(open("moex_ex_data_out.json", 'r').read())


def test_exchange_data_exc():
    with pytest.raises(moex.BadExchangeResponse):
        moex.make_request = Mock()
        moex.make_request.return_value = {}
        moex.exchange_data()
