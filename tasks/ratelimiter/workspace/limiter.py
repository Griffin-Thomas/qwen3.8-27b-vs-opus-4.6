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
