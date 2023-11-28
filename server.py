
import websockets
import json
from websockets.sync import server
import threading
from cryptoex import Cryptoex
import time


class Server:
    c = Cryptoex()
    default = {
        "timeout": 1,
        "count": 1
    }
    Errors = {
        "JSONDecodeError": "request is not JSON string",
    }

    sockets = set()
    socket_threads = dict()

    def send_exchange_data(self, exchange, websocket, thread_hash, **kwargs):
        count, timeout = kwargs.get("count", self.default["count"]), kwargs.get("timeout", self.default["timeout"])
        while (thread_hash in self.socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
            websocket.send(json.dumps(self.c.exchange_data(exchange)))
            print("ok")
            count -= 1
            time.sleep(timeout)

    def send_ticker_data(self, ticker, websocket, thread_hash, **kwargs):
        count, timeout = kwargs.get("count", self.default["count"]), kwargs.get("timeout", self.default["timeout"])
        while (thread_hash in self.socket_threads.get(kwargs['ws_id'], str(websocket.id))) and (count != 0):
            websocket.send(json.dumps(self.c.ticker_data(ticker, kwargs.get("exchange", "all"))))
            count -= 1
            time.sleep(timeout)

    def send_klines(self, ticker, exchange, websocket, thread_hash, **kwargs):
        print(self.c.klines(exchange, ticker))
        self.socket_threads[kwargs.get("ws_id",str(websocket.id))].remove(thread_hash)

    def manage(self, request, websocket):
        ws_id = str(websocket.id)
        stream_functions = {
            "exchange_stream": self.send_exchange_data,
            "klines_stream": self.send_klines,
            "ticker_stream": self.send_ticker_data
        }
        thread_hash = "&".join([x if type(x) is type(str()) else "&".join([y for y in x.values()]) for x in request.values()])
        thread_hash = hex(hash(thread_hash))
        if thread_hash in self.socket_threads[ws_id]:
            self.socket_threads[ws_id].remove(thread_hash)
            return
        self.socket_threads[ws_id].add(thread_hash)
        kwargs = {"thread_hash": thread_hash,
                  "websocket": websocket,
                  "ws_id": ws_id,
                  "count": int(request.get('amount', -1)),
                  "timeout": request.get('timeout', 1)}
        kwargs.update(request['data'])
        threading.Thread(target=stream_functions[request['type']], kwargs=kwargs).start()

    def handle(self, websocket):
        for request in websocket:
            ws_id = str(websocket.id)
            if ws_id not in self.sockets:
                self.sockets.add(ws_id)
                self.socket_threads[ws_id] = set()
            try:
                request = json.loads(request)
                print(request)
            except json.JSONDecodeError:
                error = json.dumps({"Error": self.Errors['JSONDecodeError']})
                print(error)
                continue
            self.manage(request, websocket)

    def main(self):
        with websockets.sync.server.serve(self.handle, "localhost", 8765) as server:
            print("server started")
            server.serve_forever()

    def run(self):
        self.main()


s = Server()
s.run()
