import unittest

from limiter import SlidingWindowLimiter


class FakeClock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestSlidingWindowLimiter(unittest.TestCase):
    def test_allows_up_to_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=3, window=60, clock=clock)
        for _ in range(3):
            self.assertTrue(limiter.allow("alice"))

    def test_rejects_over_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=3, window=60, clock=clock)
        for _ in range(3):
            limiter.allow("alice")
        self.assertFalse(limiter.allow("alice"))

    def test_keys_are_independent(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=1, window=60, clock=clock)
        self.assertTrue(limiter.allow("alice"))
        self.assertTrue(limiter.allow("bob"))

    def test_reset_clears_key(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=1, window=60, clock=clock)
        limiter.allow("alice")
        limiter.reset("alice")
        self.assertTrue(limiter.allow("alice"))


if __name__ == "__main__":
    unittest.main()
