# tests/fixtures/live_server.py
import socket
import threading
import time
import pytest
from werkzeug.serving import make_server


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


class _ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=None):
        super().__init__(daemon=True)
        self.host = host
        self.port = port or _free_port()
        self._srv = make_server(self.host, self.port, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"

    def run(self):
        self._srv.serve_forever()

    def shutdown(self):
        self._srv.shutdown()
        self.ctx.pop()


@pytest.fixture
def live_server(app):
    """啟一個真實的 WSGI HTTP server，支援多執行緒併發連線。"""
    server = _ServerThread(app)
    server.start()
    # 簡單等一下讓 server ready
    time.sleep(0.15)
    try:
        yield server
    finally:
        server.shutdown()
