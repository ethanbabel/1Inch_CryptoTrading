import requests
import time
import threading

class APIThrottler:
    def __init__(self, rate_limit_per_second):
        self.rate_limit = rate_limit_per_second
        self.lock = threading.Lock()  # Ensures thread-safe access to timestamps
        # self.request_timestamps = []  # Stores timestamps of previous API requests
        self.last_request_time = 0  # Track last request timestamp


    # def enforce_rate_limit(self):
    #     """Ensures that API calls comply with the rate limit."""
        # with self.lock:
        #     # Remove timestamps older than 1 second
        #     now = time.time()
        #     self.request_timestamps = [t for t in self.request_timestamps if now - t < 1]

        #     # If we exceed the rate limit, wait before proceeding
        #     if len(self.request_timestamps) >= self.rate_limit:
        #         sleep_time = 1 - (now - self.request_timestamps[0])
        #         if sleep_time > 0:
        #             time.sleep(sleep_time)

        #     # Log the new request timestamp
        #     self.request_timestamps.append(time.time())
    def enforce_rate_limit(self):
        """Ensures all fetchers respect the global rate limit."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = max(0, 1 / self.rate_limit - elapsed)  # Wait until allowed
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_request_time = time.time()  # Update last request timestamp

    # def request_with_retry(self, url, headers, params):
    #     """Makes an API request while handling rate limits and retries."""
    #     max_retries = 5
    #     retry_delay = 2  # Initial retry delay in seconds

    #     for attempt in range(max_retries):
    #         self.enforce_rate_limit()  # Apply global rate limiting
    #         response = requests.get(url, headers=headers, params=params)

    #         if response.status_code == 200:
    #             return response.json()  # Successful request
    #         elif response.status_code == 429:
    #             print(f"🚨 Rate limit exceeded. Retrying in {retry_delay} seconds...")
    #             time.sleep(retry_delay)  # Exponential backoff
    #             retry_delay *= 2  # Double wait time for each retry
    #         else:
    #             print(f"⚠️ Unexpected error: {response.status_code}")
    #             return None  # Return None if request fails

    #     print("❌ Max retries reached. Request failed.")
    #     return None  # Request failed after retries