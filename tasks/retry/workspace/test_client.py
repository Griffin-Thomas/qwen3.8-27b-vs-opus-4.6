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
