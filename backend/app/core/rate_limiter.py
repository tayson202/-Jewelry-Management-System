import time
from typing import Dict, Tuple
from fastapi import HTTPException, status, Request

class SlidingWindowRateLimiter:
    """
    Sliding-window in-memory rate limiter as specified in the
    Enterprise Security Blueprint (Section 3).
    Prevents Brute-Force, DoS, and credential stuffing.
    """
    def __init__(self, limit: int = 15, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.store: Dict[str, list] = {}

    def cleanup(self):
        now = time.time()
        for key in list(self.store.keys()):
            self.store[key] = [t for t in self.store[key] if now - t < self.window_seconds]
            if not self.store[key]:
                del self.store[key]

    def check(self, identifier: str):
        now = time.time()
        # Clean stale timestamps for this key
        timestamps = self.store.get(identifier, [])
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(valid_timestamps) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Rate limit exceeded. Try again in {self.window_seconds}s."
            )

        valid_timestamps.append(now)
        self.store[identifier] = valid_timestamps

# Pre-configured instances
auth_rate_limiter = SlidingWindowRateLimiter(limit=10, window_seconds=60)
sensitive_action_limiter = SlidingWindowRateLimiter(limit=20, window_seconds=60)

def rate_limit_auth(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(client_ip)
