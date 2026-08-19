import unittest

from client import Client, HTTPError, Response


class ScriptedTransport:
    def __init__(self, script):
        self.script = list(script)
        self.sends = []

    def send(self, method, url):
        self.sends.append((method, url))
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


class RecordingSleep:
    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)


class TestHoldoutRetry(unittest.TestCase):
    def test_recovers_from_transient_connection_errors(self):
        transport = ScriptedTransport(
            [ConnectionError("reset"), ConnectionError("reset"), Response(200, "ok")]
        )
        client = Client(transport, sleep=RecordingSleep())
        response = client.request("GET", "/things")
        self.assertEqual(response.status, 200)
        self.assertEqual(len(transport.sends), 3)

    def test_retries_server_errors(self):
        transport = ScriptedTransport([Response(503), Response(200, "ok")])
        client = Client(transport, sleep=RecordingSleep())
        self.assertEqual(client.request("GET", "/things").status, 200)

    def test_retries_rate_limit_responses(self):
        transport = ScriptedTransport([Response(429), Response(200, "ok")])
        client = Client(transport, sleep=RecordingSleep())
        self.assertEqual(client.request("GET", "/things").status, 200)

    def test_does_not_retry_client_errors(self):
        transport = ScriptedTransport([Response(400, "bad")])
        client = Client(transport, sleep=RecordingSleep())
        with self.assertRaises(HTTPError):
            client.request("POST", "/things")
        self.assertEqual(len(transport.sends), 1, "4xx must not be retried")

    def test_gives_up_eventually_but_does_retry(self):
        transport = ScriptedTransport([ConnectionError("down")])
        client = Client(transport, sleep=RecordingSleep())
        with self.assertRaises((ConnectionError, HTTPError)):
            client.request("GET", "/things")
        self.assertGreaterEqual(len(transport.sends), 2, "no retry happened")
        self.assertLessEqual(len(transport.sends), 8, "retries not bounded")

    def test_backoff_delays_are_not_constant(self):
        transport = ScriptedTransport([ConnectionError("down")])
        sleeper = RecordingSleep()
        client = Client(transport, sleep=sleeper)
        with self.assertRaises((ConnectionError, HTTPError)):
            client.request("GET", "/things")
        self.assertGreaterEqual(len(sleeper.calls), 2, "expected waits between retries")
        self.assertGreater(
            max(sleeper.calls),
            min(sleeper.calls),
            "delays never grew; backoff does not look exponential",
        )


if __name__ == "__main__":
    unittest.main()
