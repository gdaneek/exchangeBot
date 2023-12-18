import json
import threading
import websockets
from src.cryptoex import Cryptoex
from websockets.sync.server import serve
#from .moex_exchange import MoexExchange
import time

"""
 WebSocket server code file
"""
class  MoexExchange:
    class BadExchangeResponse(Exception): pass
cryptoex = Cryptoex()
"""
an instance of a class for working with crypto exchanges
"""

moex = 1 #MoexExchange()
"""
an instance of a class for working with stock exchanges
"""


#   default settings that will be used for optional parameters if the user does not specify their value in his request
default = {
        "timeout": 1,
        "count": 1,
        "interval": "1d",
        "limit": 365,
        "alive_threads_viewing_delay": .2,
        "extype": "crypto"
    }
"""
    default server settings
"""

#   the list of errors returned by the server to an incorrect request from the websocket client
Errors = {
        "WRF 0x01": "request is not JSON string",    # FE 0x01 | JSONDecodeError
        "WRF 0x02": "request is not converted to a dict",  # FE 0x01 | JSONDecodeError
        "RPM 0x01": "the required argument 'type' wasn't defined",    # | Key Error
        "RPM 0x02": "the required argument 'data' wasn't defined",    # | Key Error
        "BExR 0x01": "The exchange's response code is 400 or 404. Please check your request",
        "WPV 0x01": "some parameters have an unknown value or an incorrect value's type",  # TypeError
        "WPV 0x02": "ticker must contain `-` as a separator",
        "WPV 0x03": "unsupported or incorrect exchange",
        "WPV 0x04": "parameters 'type' and 'extype' must be str",
        "WPV 0x05": "parameters 'count' and 'timeout' must contain only numbers 0-9",
        "WPV 0x06": "parameter 'type' or 'extype' has an unknown value",
        "UnErr": "Unknown error"
    }
"""
errors returned by the server and their description
"""

#   there are a set of web clients at current moment
extypes = {
    "crypto": cryptoex,
    "stock": moex
}
"""
types of exchanges. Total 2: Crypto and Stock
"""

sockets = dict()
"""
the dictionary of websocket clients, which includes many streams of each of them
"""


def make_error_msg(key):
    """
     function that creates the error message
    :param key: the key to use to get the error message text
    :return: Error message
    :rtype: str
    """
    return f"{key}: {Errors[key]}"


# лучше делать декоратором, но непонятно как тестировать тогда
def websocket_send(websocket, func=None, thread_id=None, err_msg="", **kwargs):
    """a function that makes sending messages safe

    The function accepts a websocket, a function whose return value must be sent, and arguments for this function.
    If you need to send only an error code, the err_msg parameter must not be empty.

    :param websocket: the websocket to send the message to
    :param func: a function whose result will be a message to be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param err_msg: if it is transmitted, it contains an error message that needs to be sent
    :param kwargs: arguments of the function func
    :return: None
    """
    response, error = err_msg, True
    if len(response) > 0:
        try:
            websocket.send(response)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            remove_thread(str(websocket.id), thread_id)
            return
    try:
        response, error = json.dumps(func(**kwargs)), False
    except Cryptoex.BadResponseError:
        response = make_error_msg("BExR 0x01")
    except (TypeError, KeyError):
        response = make_error_msg("WPV 0x01")
    except Cryptoex.BadTickerError:
        response = make_error_msg("WPV 0x02")
    except Cryptoex.BadExchangeError:
        response = make_error_msg("WPV 0x03")
    except MoexExchange.BadExchangeResponse:
        response = make_error_msg("BExR 0x01")
    except Exception:
        response = make_error_msg("UnErr")
    if thread_id in sockets[str(websocket.id)]:
        try:
            websocket.send(response)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            if error:
                remove_thread(str(websocket.id), thread_id)


def remove_thread(ws_id, thread_id):
    """

    a function for safely removing a thread from the list of threads for websocket with id = websocket.id

    :param ws_id: websocket ID
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :return: -
    :rtype: None
    """
    if ws_id in sockets:
        if thread_id in sockets[ws_id]:
            sockets[ws_id].remove(thread_id)


def thread_array_is_alive(threads):
    """
    checks if there is at least one running thread in the list

    :param threads: the list of threads that need to be checked
    :return: False if all threads are completed and True if at least one of them is alive
    :rtype: bool
    """
    flag = False
    for thread in threads:
        flag |= thread.is_alive()
    return flag


def send_exchange_data(websocket, thread_id, **kwargs) -> None:
    """
    A function that sends exchange statistics (data on all tickers)
     Statistics are given for 24 hours

    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    count, timeout, threads = kwargs.get("count"), kwargs.get("timeout"), set()
    exchange = kwargs.get("exchange")
    extype = kwargs.get("extype")
    while thread_id in sockets[str(websocket.id)]:
        if count == 0:
            if not thread_array_is_alive(threads):
                remove_thread(str(websocket.id), thread_id)
            time.sleep(default["alive_threads_viewing_delay"])
            continue
        _args, _kwargs = [websocket, extype.exchange_data, thread_id], {"exchange": exchange}
        thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)
        threads.add(thread)
        thread.start()
        count -= 1
        time.sleep(timeout)


def send_ticker_data(websocket, thread_id, **kwargs) -> None:
    """
    A function that sends statistics on the specified ticker from the exchange in real time
    The data is sent in the last 24 hours

    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    count, timeout, threads = kwargs.get("count"), kwargs.get("timeout"), set()
    exchange = kwargs.get("exchange")
    ticker = kwargs.get("ticker")
    extype = kwargs.get("extype")
    while thread_id in sockets[str(websocket.id)]:
        if count == 0:
            if not thread_array_is_alive(threads):
                remove_thread(str(websocket.id), thread_id)
            time.sleep(default["alive_threads_viewing_delay"])
            continue
        _args, _kwargs = [websocket, extype.ticker_data, thread_id], {"ticker": ticker, "exchange": exchange}
        thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)
        thread.start()
        threads.add(thread)
        count -= 1
        time.sleep(timeout)


def send_klines(websocket, thread_id, **kwargs) -> None:
    """
    A function that sends data for plotting at a specified interval to a websocket client

    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    extype = kwargs.get("extype")
    interval, limit = kwargs.get("interval", default["interval"]), kwargs.get("limit", default["limit"])
    ticker, exchange = kwargs.get("ticker"), kwargs.get("exchange")
    _args = [websocket, extype.klines, thread_id]
    _kwargs = {"ticker": ticker, "interval": interval, "limit": limit}
    thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)
    thread.start()
    while thread_array_is_alive([thread]):
        time.sleep(default["alive_threads_viewing_delay"])
    remove_thread(str(websocket.id), thread_id)


stream_functions = {
            "exchange_stream": send_exchange_data,
            "klines_stream": send_klines,
            "ticker_stream": send_ticker_data}
"""
a list that matches the type of request and the function that processes it
"""


def manage(request, websocket):
    """
    A function that performs thread control and processes a request sent by the user

    :param request: request sent by the websocket client
    :param websocket: the client's websocket class
    :return: None
    """

    try:
        s_type, s_data = request['type'], request['data']
    except KeyError:
        err_msg = (make_error_msg("RPM 0x01")) if request.get("type") is None else make_error_msg("RPM 0x02")
        websocket_send(websocket, err_msg=err_msg)
        return
    try:
        extype = s_data.get("extype", default["extype"])
        if (s_type not in stream_functions) or (extype not in extypes):
            websocket_send(websocket, err_msg=make_error_msg("WPV 0x06"))
            return
        s_data['extype'] = extypes[extype]
    except TypeError:
        websocket_send(websocket, err_msg=make_error_msg("WPV 0x04"))
        return

    thread_id = hex(abs(hash(str(request))))
    if thread_id in sockets[str(websocket.id)]:
        remove_thread(str(websocket.id), thread_id)
        return
    sockets[str(websocket.id)].add(thread_id)
    try:
        count, timeout = int(request.get('count', default["count"])), float(request.get('timeout', default["timeout"]))
    except (ValueError, TypeError):
        websocket_send(websocket, err_msg=make_error_msg("WPV 0x05"))
        return

    kwargs = {
                  "thread_id": thread_id,
                  "websocket": websocket,
                  "count": count,
                  "timeout": timeout}
    kwargs.update(s_data)

    threading.Thread(target=stream_functions.get(s_type), kwargs=kwargs).start()


def handle(websocket):
    print("new client!")
    """
    A function that listens to the requests of the websocket

    :param websocket: current websocket client
    :return: None
    """
    for request in websocket:
        ws_id = str(websocket.id)

        if ws_id not in sockets:
            sockets[ws_id] = set()
        try:
            request = json.loads(request)
        except (json.JSONDecodeError, TypeError):
            websocket_send(websocket, err_msg=make_error_msg("WRF 0x01"))
            continue
        if type(request) is not dict:
            websocket_send(websocket, err_msg=make_error_msg("WRF 0x02"))
            continue
        manage(request, websocket)


if __name__ == "__main__":
    with serve(handle, "127.0.0.1", 8765) as ws_server:
        print("server started")
        ws_server.serve_forever()
