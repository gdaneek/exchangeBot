import websockets
import json
from websockets.sync import server
import threading
from cryptoex import Cryptoex
import time

cryptoex = Cryptoex()

#   default settings that will be used for optional parameters if the user does not specify their value in his request
default = {
        "timeout": 1,
        "count": 1,
        "interval": "1d",
        "limit": 365,
        "alive_threads_viewing_delay": .2 # настройка сервера , задержка при просмотре живых потоков
    }

#   the list of errors returned by the server to an incorrect request from the websocket client
Errors = {
        "WRF 0x01": "request is not JSON string",    # FE 0x01 | JSONDecodeError
        "RPM 0x01": "the required argument 'type' wasn't defined",    # | Key Error
        "RPM 0x02": "the required argument 'data' wasn't defined",    # | Key Error
        "BExR 0x01": "The exchange's response code is 400 or 404. Please check your request",    # Cryptoex.BadRequestError
        "WPV 0x01": "some parameters have an unknown value or an incorrect value's type",  # TypeError
        "WPV 0x02": "ticker must contain `-` as a separator",
    }

#   there are a set of web clients at current moment


sockets = dict()


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
    if len(err_msg) > 0:
        try:
            websocket.send(err_msg)
        except websockets.exceptions.ConnectionClosedOK: pass
        finally:
            return
    error = True
    try:
        response, error = json.dumps(func(**kwargs)), False
    except Cryptoex.BadRequestError:
        response = Errors["BExR 0x01: "+Errors["BExR 0x01"]]
    except (TypeError, KeyError):
        response = Errors["WPV 0x01: "+Errors["WPV 0x01"]]
    except Cryptoex.BadTickerError:
        response = Errors["WPV 0x02: "+Errors["WPV 0x02"]]
    if thread_id in sockets[str(websocket.id)]:      # если поступит запрос на отмену потока
        try:
            websocket.send(response)
        except websockets.exceptions.ConnectionClosedOK: pass
        finally:
            if error:
                remove_thread(str(websocket.id), thread_id)


def remove_thread(ws_id, thread_id):
    """

    a function for safely removing a thread from the list of threads for websocket with id = websocket.id

    :param ws_id: websocket ID
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :return:
    """
    if ws_id in sockets:
        if thread_id in sockets[ws_id]:
            sockets[ws_id].remove(thread_id)
            #print("thread removed")


def thread_array_is_alive(threads):
    """

    :param threads: the list of threads that need to be checked
    :return: False if all threads are completed and True if at least one of them is alive
    :rtype: bool
    """
    flag = False
    for thread in threads:
        flag |= thread.is_alive()
    return flag


def send_exchange_data(exchange, websocket, thread_id, **kwargs):
    """
    A function that sends exchange statistics (data on all tickers)
     Statistics are given for 24 hours

    :param exchange: the exchange from which data should be received
    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    count, timeout, threads = kwargs.get("count"), kwargs.get("timeout"), set()
    while thread_id in sockets[str(websocket.id)]:
        if count == 0:
            if not thread_array_is_alive(threads):
                remove_thread(str(websocket.id), thread_id)
            time.sleep(default["alive_threads_viewing_delay"])
            continue
        _args, _kwargs = [websocket, cryptoex.exchange_data, thread_id], {"exchange": exchange}
        thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)   # тут не надо исключения
        thread.start()
        threads.add(thread)
        count -= 1
        time.sleep(timeout)


def send_ticker_data(websocket, thread_id, **kwargs):
    """
    A function that sends statistics on the specified ticker from the exchange in real time
    The data is sent in the last 24 hours

    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    count, timeout, threads = kwargs.get("count"), kwargs.get("timeout"), set()
    exchanges = cryptoex.exchanges.keys() if kwargs.get("exchange") is None else [kwargs.get("exchange")]
    ticker = kwargs.get("ticker")
    # когда count == 0, переходим в режим ожидания завершения всех потоков
    while thread_id in sockets[str(websocket.id)]: # если count < 0 - бесконечный цикл
        if count == 0:         #  если count == 0 - будем ждать, когда завершатся все запушенные потоки
            if not thread_array_is_alive(threads):
                remove_thread(str(websocket.id), thread_id)
            time.sleep(default["alive_threads_viewing_delay"]) # ждать, пока все потоки закончатся, после чего завершить работу
            continue
        for exchange in exchanges:
            print(exchange)
            _args, _kwargs = [websocket, cryptoex.ticker_data, thread_id], {"ticker": ticker, "exchange": exchange}
            thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)  # тут не надо исключения
            thread.start()
            threads.add(thread)
        count -= 1
        time.sleep(timeout)


def send_klines(websocket, thread_id, **kwargs):
    """
    A function that sends data for plotting at a specified interval to a websocket client

    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    interval, limit = kwargs.get("interval", default["interval"]), kwargs.get("limit", default["limit"])
    ticker, exchange = kwargs.get("ticker"), kwargs.get("exchange")
    _args, _kwargs = [websocket, cryptoex.klines, thread_id], {"ticker": ticker, "exchange": exchange, "interval": interval, "limit": limit}
    thread = threading.Thread(target=websocket_send, args=_args, kwargs=_kwargs)  # тут не надо исключения
    thread.start()
    while thread_array_is_alive([thread]):
        time.sleep(default["alive_threads_viewing_delay"])
    remove_thread(str(websocket.id), thread_id)


stream_functions = {
            "exchange_stream": send_exchange_data,
            "klines_stream": send_klines,
            "ticker_stream": send_ticker_data}


def manage(request, websocket):
    """
    A function that performs thread control and processes a request sent by the user

    :param request: request sent by the websocket client
    :param websocket: the client's websocket class
    :return: None
    """
    try:
        s_type = request['type']
    except KeyError:
        websocket_send(websocket, err_msg="RPM 0x01: "+Errors["RPM 0x01"])
        return
    try:
        s_data = request['data']
    except KeyError:
        websocket_send(websocket, err_msg="RPM 0x02: " + Errors["RPM 0x02"])
        return
    thread_id = hex(abs(hash(str(request))))
    if thread_id in sockets[str(websocket.id)]:
        remove_thread(str(websocket.id), thread_id)
        return
    sockets[str(websocket.id)].add(thread_id)
    kwargs = {
                  "thread_id": thread_id,
                  "websocket": websocket,
                  "count": int(request.get('count', default["count"])),
                  "timeout": int(request.get('timeout', default["timeout"]))}
    kwargs.update(s_data)
    threading.Thread(target=stream_functions[s_type], kwargs=kwargs).start()


def handle(websocket):
    """
    A function that listens to the requests of the websocket

    :param websocket: current websocket client
    :return: None
    """
    for request in websocket:
        ws_id = str(websocket.id)
        if ws_id not in sockets:
            sockets[ws_id] = set()
        print(request)
        try:
            request = json.loads(request)
        except json.JSONDecodeError:
            websocket.send('WRF 0x01: '+Errors['WRF 0x01'])
            continue
        manage(request, websocket)


def main():
    """
    The main function that starts the synchronous server on port 8765

    :return: None
    """
    with websockets.sync.server.serve(handle, "localhost", 8765) as server:
        print("server started")
        server.serve_forever()


main()
