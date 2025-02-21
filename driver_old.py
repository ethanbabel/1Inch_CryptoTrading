import threading
import time
import copy
from price_fetcher import PriceFetcher
from arb_detector import ArbitrageDetector

class Driver:
    def __init__(self):
        self.price_fetcher = PriceFetcher()
        self.master_graph = {}  # Shared graph (only modified by price fetchers)
        self.lock = threading.Lock()  # Lock only for copying the latest graph

    def update_prices(self):
        """Continuously fetch price data and update the master graph."""
        while True:
            new_graph = self.price_fetcher.update_prices()

            with self.lock:  # Acquire lock only for updating master_graph
                print("🔄 Updating token prices...")
                self.master_graph = new_graph

            print("✅ Prices updated.")
            time.sleep(1)  # Rate-limited API calls

    def detect_arbitrage(self):
        """Continuously check for arbitrage opportunities using a copy of the graph."""
        while True:
            with self.lock:  # Acquire lock only briefly to copy master_graph
                print("Arbitrage detection in progress...")
                graph_snapshot = copy.deepcopy(self.master_graph)

            if graph_snapshot:
                detector = ArbitrageDetector(graph_snapshot)
                opportunities = detector.detect_arbitrage()
                for opp in opportunities:
                    detector.log_arbitrage_opportunity(opp)
                    detector.send_arbitrage_email(opp)

            time.sleep(2)  # Avoid overloading computations

    def run(self):
        """Starts price fetching and arbitrage detection in parallel threads."""
        price_thread = threading.Thread(target=self.update_prices, daemon=True)
        arb_thread = threading.Thread(target=self.detect_arbitrage, daemon=True)

        price_thread.start()
        arb_thread.start()

        price_thread.join()
        arb_thread.join()

if __name__ == "__main__":
    driver = Driver()
    driver.run()