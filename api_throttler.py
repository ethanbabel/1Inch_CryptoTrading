import time
import threading

class APIThrottler:
    def __init__(self, rate_limit_per_second):
        self.rate_limit = rate_limit_per_second
        self.lock = threading.Lock()  # Ensures thread-safe access to timestamps
        # self.request_timestamps = []  # Stores timestamps of previous API requests
        self.last_request_time = 0  # Track last request timestamp

    def enforce_rate_limit(self):
        """Ensures all fetchers respect the global rate limit."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = max(0, 1 / self.rate_limit - elapsed)  # Wait until allowed
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_request_time = time.time()  # Update last request timestamp