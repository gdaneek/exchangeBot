
import websockets
import json
from websockets.sync import server
import threading
from cryptoex import Cryptoex
import time

cryptoex = Cryptoex()


default = {
        "timeout": 1,
        "count": 1
    }
Errors = {
        "JSONDecodeError": "request is not JSON string",
    }

sockets = set()
socket_threads = dict()


def send_exchange_data(exchange, websocket, thread_hash, **kwargs):
    count, timeout = kwargs.get("count", default["count"]), kwargs.get("timeout", default["timeout"])
    while (thread_hash in socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
        websocket.send(json.dumps(cryptoex.exchange_data(exchange)))
        count -= 1
        time.sleep(timeout)


def send_ticker_data(ticker, websocket, thread_hash, **kwargs):
    count, timeout = kwargs.get("count", default["count"]), kwargs.get("timeout", default["timeout"])
    while (thread_hash in socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
        websocket.send(json.dumps(cryptoex.ticker_data(ticker, kwargs.get("exchange", "all"))))
        count -= 1
        time.sleep(timeout)


def send_klines(ticker, exchange, websocket, thread_hash, **kwargs):
    socket_threads[kwargs.get("ws_id", str(websocket.id))].remove(thread_hash)


def manage(request, websocket):
    ws_id = str(websocket.id)
    stream_functions = {
            "exchange_stream": send_exchange_data,
            "klines_stream": send_klines,
            "ticker_stream": send_ticker_data
        }
    thread_hash = "&".join([x if type(x) is type(str()) else "&".join([y for y in x.values()]) for x in request.values()])
    thread_hash = hex(hash(thread_hash))
    if thread_hash in socket_threads[ws_id]:
        socket_threads[ws_id].remove(thread_hash)
        return
    socket_threads[ws_id].add(thread_hash)
    kwargs = {
                  "thread_hash": thread_hash,
                  "websocket": websocket,
                  "ws_id": ws_id,
                  "count": int(request.get('amount', -1)),
                  "timeout": request.get('timeout', 1)}
    kwargs.update(request['data'])
    threading.Thread(target=stream_functions[request['type']], kwargs=kwargs).start()


def handle(websocket):
    for request in websocket:
        ws_id = str(websocket.id)
        if ws_id not in sockets:
            sockets.add(ws_id)
            socket_threads[ws_id] = set()
        try:
            request = json.loads(request)
        except json.JSONDecodeError:
            error = json.dumps({"Error": Errors['JSONDecodeError']})
            print(error)
            continue
        manage(request, websocket)


def main():
    with websockets.sync.server.serve(handle, "localhost", 8765) as server:
        print("server started")
        server.serve_forever()


main()
