# Task: retry

## Prompt given to both agents

This client talks to an internal API that has occasional blips: dropped connections, brief 5xx storms, and rate-limit responses. Right now any blip fails the whole request.

Add retry with exponential backoff. Use your judgment about which failures are worth retrying and about sensible defaults. Keep the existing public interface working: Client(transport) and .request(method, url) as used by existing callers, and use the injected sleep for any waiting so tests stay fast.

Existing tests must pass, and add tests for the new behaviour (python3 -m unittest). Work autonomously; do not ask questions.

## Baseline project (before either agent ran)

### client.py
```python
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
```

### test_client.py
```python
import unittest

from client import Client, HTTPError, Response


class ScriptedTransport:
    """Returns or raises each scripted item in order; repeats the last one."""

    def __init__(self, script):
        self.script = list(script)
        self.sends = []

    def send(self, method, url):
        self.sends.append((method, url))
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


class TestClient(unittest.TestCase):
    def test_success_passthrough(self):
        transport = ScriptedTransport([Response(200, "ok")])
        client = Client(transport, sleep=lambda s: None)
        response = client.request("GET", "/things")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, "ok")

    def test_client_error_raises(self):
        transport = ScriptedTransport([Response(404, "missing")])
        client = Client(transport, sleep=lambda s: None)
        with self.assertRaises(HTTPError) as ctx:
            client.request("GET", "/things/9")
        self.assertEqual(ctx.exception.status, 404)

    def test_unrecoverable_network_failure_raises(self):
        transport = ScriptedTransport([ConnectionError("refused")])
        client = Client(transport, sleep=lambda s: None)
        with self.assertRaises(ConnectionError):
            client.request("GET", "/things")


if __name__ == "__main__":
    unittest.main()
```
