# Task: ratelimiter

## Prompt given to both agents

Two customer-facing problems have been reported against this rate limiter and support has confirmed both:

1. Customers who briefly exceed their limit report staying blocked indefinitely, even after they back off well below their allowed rate. The only workaround support has found is deleting the customer's key.

2. Separately, monitoring occasionally shows short bursts where more requests than the configured limit get through in a window.

Find and fix the causes. The existing tests must still pass (python3 -m unittest), and please add regression tests for what you fix. Work autonomously; do not ask questions.

## Baseline project (before either agent ran)

### limiter.py
```python
"""Per-key sliding-window rate limiting for the public API tier."""

import time


class SlidingWindowLimiter:
    """Allow at most `limit` requests per `window` seconds for each key.

    A `clock` callable can be injected for testing; it must return seconds
    as a float, like time.time.
    """

    def __init__(self, limit, window, clock=time.time):
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._hits = {}

    def allow(self, key):
        """Record an attempt for `key` and return whether it is allowed."""
        now = int(self.clock())
        hits = self._hits.setdefault(key, [])
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.pop(0)
        allowed = len(hits) < self.limit
        hits.append(now)
        return allowed

    def reset(self, key):
        """Forget all recorded attempts for `key`."""
        self._hits.pop(key, None)
```

### test_limiter.py
```python
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
```
