import threading
import pytest
from unittest.mock import Mock
import ws_server as s
import json
from cryptoex import Cryptoex
test_request = {"type": "ticker_stream", "data": {"ticker": "BTC-USDT", "exchange": "Bybit"}, "timeout": 10, "count": 5}


class SocketConnection:
    """
        a class that emulates a connection to a websocket client
    """

    def __init__(self):
        self.id = "0x123FF"
        self.requests = [json.dumps({'type': 'test_request'})]
        self.i = 0

    def send(self, msg): pass

    def __iter__(self):
        return self

    def __next__(self):
        self.i += 1
        if self.i <= len(self.requests):
            return self.requests[self.i - 1]
        else:
            self.i = 0
            raise StopIteration()


# ------------------------  websocket_send testing ------------------------ #
class Exc:
    """
        the class is a generator of functions that throw all kinds of exceptions for the server
    """
    exceptions = [Cryptoex.BadResponseError, TypeError, TypeError,
                  Cryptoex.BadTickerError, Cryptoex.BadExchangeError, Exception]
    i = 0

    def f(self, exc):
        raise exc()

    def get_exc_func(self):
        self.i += 1
        if self.i == len(self.exceptions) + 1:
            return
        return self.f, self.exceptions[self.i - 1]


exc_ = Exc()


def test_websocket_send_func_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    websocket.send = Mock()

    def f(**kwargs): return {"data": "some data..."}
    s.websocket_send(websocket=websocket, func=f, thread_id="0x01")
    websocket.send.assert_called_with(json.dumps({"data": "some data..."}))


def test_websocket_send_err_msg():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    websocket.send = Mock()
    s.websocket_send(websocket, thread_id="0x01", err_msg='some err...')

    websocket.send.assert_called_with('some err...')
    assert ("0x01" not in s.sockets[websocket.id]) is True


def test_websocket_send_func_all_exc():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    s.sockets[websocket.id].add("0x02")
    call_args, all_ok = [], True
    expected_answers = [s.make_error_msg("BExR 0x01"), s.make_error_msg("WPV 0x01"),
                        s.make_error_msg("WPV 0x01"), s.make_error_msg("WPV 0x02"),
                        s.make_error_msg("WPV 0x03"), s.make_error_msg("UnErr")]
    websocket.send = Mock()
    for i in range(len(exc_.exceptions)):
        f, e = exc_.get_exc_func()
        s.websocket_send(websocket=websocket, func=f, thread_id="0x01", err_msg="", exc=e)
        s.sockets[websocket.id].add("0x01")
        call_args.append(websocket.send.call_args)
    for i in range(len(call_args)):
        all_ok &= (call_args[i].__str__().replace('"', "'") == f"call('{expected_answers[i]}')")

    assert (websocket.send.call_count == len(exc_.exceptions)) and (all_ok is True)


# ------------------------  manage testing ------------------------ #

def test_manage_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    threading.Thread = Mock()
    s.manage(test_request, websocket)
    _kwargs = {'thread_id':  hex(abs(hash(str(test_request)))), 'websocket': websocket, 'count': 5,
               'timeout': 10, 'ticker': 'BTC-USDT', 'exchange': 'Bybit', "extype": s.extypes[s.default["extype"]]}

    threading.Thread.assert_called_with(target=s.stream_functions[test_request['type']], kwargs=_kwargs)


def test_manage_required_parameter_type_missed():
    websocket = SocketConnection()
    t = test_request.copy()
    t.pop("type")
    s.websocket_send = Mock()
    s.manage(t, websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("RPM 0x01"))


def test_manage_required_parameter_data_missed():
    websocket = SocketConnection()
    t = test_request.copy()
    t.pop("data")
    s.websocket_send = Mock()
    s.manage(t, websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("RPM 0x02"))


def test_manage_wpv0x04():
    websocket = SocketConnection()
    t = test_request.copy()
    t['type'] = {}
    s.websocket_send = Mock()
    s.manage(t, websocket)
    s.websocket_send.assert_called_with(websocket,  err_msg=s.make_error_msg("WPV 0x04"))


def test_manage_wpv0x05_bad_count_or_timeout_value_type():
    websocket = SocketConnection()
    t = test_request.copy()
    t['count'], t['data']['extype'] = {}, "crypto"
    s.websocket_send = Mock()
    s.manage(t, websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("WPV 0x05"))

# ------------------------  send_ticker_data, send_exchange_data and send_klines testing ------------------------ #


send_ticker_data_kwargs = {'count': 5, 'timeout': 0, 'ticker': 'BTC-USDT',
                           'exchange': 'Bybit', 'extype': s.cryptoex}

send_exchange_data_kwargs = {'count': 5, 'timeout': 0, 'exchange': 'Bybit', 'extype': s.cryptoex}

send_klines_kwargs = {'count': 1, 'timeout': 0, 'ticker': 'BTC-USDT', 'extype': s.cryptoex}


def test_send_ticker_data_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    threading.Thread = Mock()
    s.websocket_send = Mock()
    s.thread_array_is_alive = Mock()
    s.thread_array_is_alive.return_value = False
    s.send_ticker_data(websocket, "0x01", **send_ticker_data_kwargs)
    _args = [websocket, s.cryptoex.ticker_data, "0x01"]
    _kwargs = {"ticker": send_ticker_data_kwargs['ticker'], "exchange":  send_ticker_data_kwargs['exchange']}

    threading.Thread.assert_called_with(target=s.websocket_send, args=_args, kwargs=_kwargs)
    assert threading.Thread.call_count == send_ticker_data_kwargs['count']


def test_send_exchange_data_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    threading.Thread = Mock()
    s.websocket_send = Mock()
    s.thread_array_is_alive = Mock()
    s.thread_array_is_alive.return_value = False
    s.send_exchange_data(websocket, "0x01", **send_exchange_data_kwargs)
    _args = [websocket, s.cryptoex.exchange_data, "0x01"]
    _kwargs = {"exchange": send_exchange_data_kwargs['exchange']}

    threading.Thread.assert_called_with(target=s.websocket_send, args=_args, kwargs=_kwargs)
    assert threading.Thread.call_count == send_exchange_data_kwargs['count']


def test_send_klines_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    threading.Thread = Mock()
    s.websocket_send = Mock()
    s.thread_array_is_alive = Mock()
    s.thread_array_is_alive.return_value = False
    s.send_klines(websocket, "0x01", **send_klines_kwargs)
    _args = [websocket, s.cryptoex.klines, "0x01"]
    _kwargs = {"ticker": send_klines_kwargs['ticker'],
               "interval": s.default['interval'],
               "limit": s.default['limit']
               }

    threading.Thread.assert_called_with(target=s.websocket_send, args=_args, kwargs=_kwargs)
    assert threading.Thread.call_count == send_klines_kwargs['count']

# ------------------------  handle testing ------------------------ #


def test_handle_successful_one_request():
    websocket = SocketConnection()
    s.manage = Mock()
    s.handle(websocket)
    s.manage.assert_called_with(json.loads(websocket.requests[0]), websocket)


def test_handle_successful_many_requests():
    websocket = SocketConnection()
    websocket.requests.append(json.dumps({'type': 'test_request 2'}))
    s.manage = Mock()
    s.handle(websocket)
    assert s.manage.call_count == len(websocket.requests)


def test_handle_wrf0x01_type_error():
    websocket = SocketConnection()
    websocket.requests = [1]
    s.manage, s.websocket_send = Mock(), Mock()
    s.handle(websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("WRF 0x01"))


def test_handle_wrf0x01_json_decode_error():
    websocket = SocketConnection()
    websocket.requests = [json.dumps({'type': '123'})+"}"]
    s.manage, s.websocket_send = Mock(), Mock()
    s.handle(websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("WRF 0x01"))


def test_handle_wrf0x02_request_is_not_dict():
    websocket = SocketConnection()
    websocket.requests = [json.dumps("1")]
    s.manage, s.websocket_send = Mock(), Mock()
    s.handle(websocket)
    s.websocket_send.assert_called_with(websocket, err_msg=s.make_error_msg("WRF 0x02"))


# ------------------------  remove_thread testing ------------------------ #

def test_remove_thread_successful():
    websocket = SocketConnection()
    s.sockets[websocket.id] = set()
    s.sockets[websocket.id].add("0x01")
    s.remove_thread(websocket.id, "0x01")
    assert "0x01" not in s.sockets[websocket.id]


def test_remove_thread_no_websocket_in_dict():
    s.remove_thread("12345", "0x01")


# ------------------------  make_error_msg testing ------------------------ #
def test_make_error_msg_successful():
    wrf0x01 = "WRF 0x01: request is not JSON string"
    assert wrf0x01 == s.make_error_msg("WRF 0x01")
