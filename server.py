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
        "limit": 365
    }

#   the list of errors returned by the server to an incorrect request from the websocket client
Errors = {
        "JSONDecodeError": "request is not JSON string",
    }

#   there are a set of web clients at current moment
sockets = set()


socket_threads = dict()


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
    count, timeout = kwargs.get("count", default["count"]), kwargs.get("timeout", default["timeout"])
    while (thread_id in socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
        websocket.send(json.dumps(cryptoex.exchange_data(exchange)))
        count -= 1
        time.sleep(timeout)


def send_ticker_data(ticker, websocket, thread_id, **kwargs):
    """
    A function that sends statistics on the specified ticker from the exchange in real time
    The data is sent in the last 24 hours

    :param ticker: ticker to send information about
    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    count, timeout = kwargs.get("count", default["count"]), kwargs.get("timeout", default["timeout"])
    while (thread_id in socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
        websocket.send(json.dumps(cryptoex.ticker_data(ticker, kwargs.get("exchange", "all"))))
        count -= 1
        time.sleep(timeout)


def send_klines(exchange, ticker, websocket, thread_id, **kwargs):
    """
    A function that sends data for plotting at a specified interval to a websocket client

    :param exchange: the exchange from which data should be received
    :param ticker: ticker to send information about
    :param websocket: websocket client to which the response should be sent
    :param thread_id: the ID of the thread used by manage function to manage the list of threads
    :param kwargs: some optional arguments that can be set by default (e.g. timeout, ws_id)
    :return: None
    """
    interval, limit = kwargs.get("interval", default["interval"]), kwargs.get("limit", default["limit"])
    websocket.send(cryptoex.klines(exchange, ticker, interval, limit))
    socket_threads[kwargs.get("ws_id", str(websocket.id))].remove(thread_id)


def manage(request, websocket):
    """
    A function that performs thread control and processes a request sent by the user

    :param request: request sent by the websocket client
    :param websocket: the client's websocket class
    :return: None
    """
    ws_id = str(websocket.id)
    stream_functions = {
            "exchange_stream": send_exchange_data,
            "klines_stream": send_klines,
            "ticker_stream": send_ticker_data}
    thread_id = "&".join([x if type(x) is str else "&".join([y for y in x.values()]) for x in request.values()])
    thread_id = hex(hash(thread_id))
    if thread_id in socket_threads[ws_id]:
        socket_threads[ws_id].remove(thread_id)
        return
    socket_threads[ws_id].add(thread_id)
    kwargs = {
                  "thread_id": thread_id,
                  "websocket": websocket,
                  "ws_id": ws_id,
                  "count": int(request.get('amount', -1)),
                  "timeout": request.get('timeout', 1)}
    kwargs.update(request['data'])
    threading.Thread(target=stream_functions[request['type']], kwargs=kwargs).start()


def handle(websocket):
    """

    :param websocket: current websocket client
    :return: None
    """
    for request in websocket:
        ws_id = str(websocket.id)
        if ws_id not in sockets:
            sockets.add(ws_id)
            socket_threads[ws_id] = set()
        try:
            request = json.loads(request)
        except json.JSONDecodeError:
            error = json.dumps({"Error": Errors['JSONDecodeError'], "code": 400})
            websocket.send(error)
            print(error)
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
