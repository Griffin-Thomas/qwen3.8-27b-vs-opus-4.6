"""Thin HTTP client wrapper around a pluggable transport."""

import time


class HTTPError(Exception):
    def __init__(self, status, body=""):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


class Response:
    def __init__(self, status, body=""):
        self.status = status
        self.body = body


class Client:
    """Issues requests through a transport.

    `transport.send(method, url)` returns a Response or raises
    ConnectionError for network-level failures. `sleep` is injectable
    for testing.
    """

    def __init__(self, transport, sleep=time.sleep):
        self.transport = transport
        self.sleep = sleep

    def request(self, method, url):
        response = self.transport.send(method, url)
        if response.status >= 400:
            raise HTTPError(response.status, response.body)
        return response
