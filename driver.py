import threading
import time
import queue
import itertools
import copy
from price_fetcher import PriceFetcher
from arb_detector import ArbitrageDetector
from api_throttler import APIThrottler

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

if __name__ == "__main__":
    # Define token addresses
    tokens = {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "BNB": "0xb8c77482e45f1f44de1745f52c74426c631bdd52",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
    }

    # Generate all unique token pairs
    token_pairs = list(itertools.combinations(tokens.items(), 2))  # List of ((ticker1, address1), (ticker2, address2))

    # Convert list of tuples to list of (ticker, address) pairs
    token_pairs = [(t1[0], t1[1], t2[0], t2[1]) for t1, t2 in token_pairs]  # Convert to (ticker1, address1, ticker2, address2)

    # Distribute token pairs evenly among fetchers
    num_fetchers = 3  # Adjust as needed
    fetcher_token_pairs = [token_pairs[i::num_fetchers] for i in range(num_fetchers)]

    rate_limit = 0.5 # Max requests per second

    driver = Driver(fetcher_token_pairs, rate_limit)
    driver.run()