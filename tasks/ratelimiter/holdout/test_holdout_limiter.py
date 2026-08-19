import unittest

from limiter import SlidingWindowLimiter


class FakeClock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now


class TestHoldoutLimiter(unittest.TestCase):
    def test_client_recovers_after_backing_off(self):
        """A client that keeps attempting below the limit must eventually
        be allowed again; rejected attempts must not extend the block."""
        clock = FakeClock(1000.0)
        limiter = SlidingWindowLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(limiter.allow("alice"))
        allowed_again = False
        for i in range(8):
            clock.now = 1000.0 + 5.0 + 6.0 * i  # one attempt every 6s
            if limiter.allow("alice"):
                allowed_again = True
                break
        self.assertTrue(
            allowed_again,
            "client attempting every 6s with limit=1/window=10s stayed blocked",
        )

    def test_no_burst_above_limit_at_fractional_boundaries(self):
        clock = FakeClock(1000.4)
        limiter = SlidingWindowLimiter(limit=2, window=1, clock=clock)
        self.assertTrue(limiter.allow("alice"))
        clock.now = 1000.6
        self.assertTrue(limiter.allow("alice"))
        clock.now = 1001.2
        self.assertFalse(
            limiter.allow("alice"),
            "third request 0.8s after the first must be rejected (limit=2/1s)",
        )

    def test_limit_holds_in_every_sliding_window(self):
        clock = FakeClock(2000.0)
        limiter = SlidingWindowLimiter(limit=3, window=5, clock=clock)
        allowed_times = []
        t = 2000.0
        while t < 2030.0:
            clock.now = t
            if limiter.allow("alice"):
                allowed_times.append(t)
            t += 0.7
        for start in allowed_times:
            in_window = [a for a in allowed_times if start <= a <= start + 4.99]
            self.assertLessEqual(
                len(in_window),
                3,
                f"{len(in_window)} requests allowed within 5s starting {start}",
            )

    def test_still_rejects_over_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=3, window=60, clock=clock)
        results = [limiter.allow("alice") for _ in range(4)]
        self.assertEqual(results, [True, True, True, False])


if __name__ == "__main__":
    unittest.main()
