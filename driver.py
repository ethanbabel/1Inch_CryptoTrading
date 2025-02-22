import threading
import time
import queue
import itertools
import copy
import pandas as pd
from dotenv import load_dotenv
import os
import requests
from price_fetcher import PriceFetcher
from arb_detector import ArbitrageDetector
from api_throttler import APIThrottler

load_dotenv()
ONEINCH_API_KEY = os.getenv("1INCH_API_KEY")

class Driver:
    def __init__(self, token_groups, rate_limit):
        self.token_groups = token_groups  # List of dictionaries {ticker: address} for each fetcher
        self.master_graph = {}  # Shared graph storing all prices
        self.lock = threading.Lock()  # Lock for updating master_graph
        self.update_queue = queue.Queue()  # Thread-safe queue for fetcher updates
        self.detector = None  # Arbitrage detector (initialized after first price update)
        self.throttler = APIThrottler(rate_limit)  # Global API throttler

    def update_prices(self, token_subset):
        """Fetch price data for a subset of tokens and push updates to the queue."""
        fetcher = PriceFetcher(token_subset, self.throttler)
        while True:
            new_graph = fetcher.update_prices()  # Fetch prices for assigned tokens
            self.update_queue.put(new_graph)  # Push to queue (thread-safe)
            # time.sleep(1)  # Rate limit API calls

    def merge_updates(self):
        """Continuously merges price updates from fetchers into the master graph."""
        while True:
            while not self.update_queue.empty():
                new_data = self.update_queue.get()  # Fetch new updates from queue
                with self.lock:  # Lock only while merging updates
                    for token, neighbors in new_data.items():
                        if token not in self.master_graph:
                            self.master_graph[token] = {}
                        self.master_graph[token].update(neighbors)  # Merge prices
            time.sleep(1)  # Adjust merge frequency as needed

    def detect_arbitrage(self):
        """Continuously check for arbitrage opportunities using a copy of the graph."""
        while True:
            with self.lock:
                graph_snapshot = copy.deepcopy(self.master_graph)

            if graph_snapshot:
                detector = ArbitrageDetector(graph_snapshot)
                opportunities = detector.detect_arbitrage()
                for opp in opportunities:
                    detector.log_arbitrage_opportunity(opp)

            time.sleep(2)  # Avoid overloading computations

    def run(self):
        """Starts multiple price fetchers, an update manager, and arbitrage detection in parallel threads."""
        fetcher_threads = [
            threading.Thread(target=self.update_prices, args=(subset,), daemon=True)
            for subset in self.token_groups
        ]
        update_thread = threading.Thread(target=self.merge_updates, daemon=True)
        arb_thread = threading.Thread(target=self.detect_arbitrage, daemon=True)

        # Start all threads
        for thread in fetcher_threads:
            thread.start()
        update_thread.start()
        arb_thread.start()

        # Join threads
        for thread in fetcher_threads:
            thread.join()
        update_thread.join()
        arb_thread.join()

def get_available_tokens():
    """Fetch the list of tokens supported by 1inch."""
    url = "https://api.1inch.dev/swap/v6.0/1/tokens"
    headers = {
        "Authorization": f"Bearer {ONEINCH_API_KEY}",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    time.sleep(1)  # Rate limit API calls
        
    if response.status_code == 200:
        data = response.json()
        return {token: details["address"] for token, details in data["tokens"].items()}
    else:
        print(f"⚠️ Failed to fetch available tokens from 1inch. Status: {response.status_code}")
        return {}


if __name__ == "__main__":
    # Load all tokens from CSV
    tokens_df = pd.read_csv("tokens_data/tokens_database_with_decimals.csv")
    all_tokens = dict(zip(tokens_df["ticker"], tokens_df["address"]))

    print(f"📊 Loaded {len(all_tokens)} tokens from CSV.")

    # Get supported tokens from 1inch
    available_tokens = get_available_tokens()

    print(f"🔍 Fetched {len(available_tokens)} tokens supported by 1inch.")

    # Filter out tokens that are not supported on 1inch
    filtered_tokens = {symbol: address for symbol, address in all_tokens.items() if address in available_tokens}
    
    print(f"✅ {len(filtered_tokens)} tokens have liquidity on 1inch.")

    # Generate valid token pairs
    token_pairs = list(itertools.combinations(filtered_tokens.items(), 2))

    # Convert pairs into (symbol1, address1, symbol2, address2)
    token_pairs = [(t1[0], t1[1], t2[0], t2[1]) for t1, t2 in token_pairs]

    # Configure number of fetchers
    num_fetchers = min(5, len(token_pairs))

    # Distribute token pairs evenly among fetchers
    fetcher_token_pairs = [token_pairs[i::num_fetchers] for i in range(num_fetchers)]

    print(f"🚀 Starting with {num_fetchers} fetchers, each handling ~{len(fetcher_token_pairs[0])} pairs.")

    # Define API rate limit per fetcher
    rate_limit = 0.5

    # Initialize and start driver
    driver = Driver(fetcher_token_pairs, rate_limit)
    driver.run()