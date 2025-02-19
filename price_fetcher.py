import requests
import json
import time
import os
from dotenv import load_dotenv
import csv

load_dotenv()
ONEINCH_API_KEY = os.getenv("1Inch_API_KEY")

# 1inch API Configuration
CHAIN_ID = 1  # Ethereum Mainnet
BASE_URL = f"https://api.1inch.dev"
SWAP_URL = f"{BASE_URL}/swap/v6.0/{CHAIN_ID}"
HEADERS = {
    "Authorization": f"Bearer {ONEINCH_API_KEY}",
    "accept": "application/json"
}

# EXAMPLE_TOKENS = {
#     "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
#     "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
#     "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
# }

class PriceFetcher:
    def __init__(self, token_pairs):
        self.graph = {}  # Adjacency list representation of token exchange rates
        self.token_pairs = token_pairs

    def get_available_tokens(self):
        """Fetch the list of tokens available for swapping in 1inch Aggregation Protocol."""
        url = f"{SWAP_URL}/tokens"
        try:
            response = requests.get(url, headers=HEADERS)
            time.sleep(1)  # Rate limit to avoid API errors
            data = response.json()
            return data.get("tokens")
        except Exception as e:
            print(f"Error fetching available tokens: {e}")
            return None

    def get_liquidity_sources(self):
        """Fetch the list of available liquidity sources (DEXs) for swaps."""
        url = f"{SWAP_URL}/liquidity-sources"
        try:
            response = requests.get(url, headers=HEADERS)
            time.sleep(1)  # Rate limit to avoid API errors
            data = response.json()
            return data.get("protocols")
        except Exception as e:
            print(f"Error fetching liquidity sources: {e}")
            return None

    def get_swap_quote(self, from_token, to_token, amount=1000000):
        """Fetch the best swap price from 1inch API."""
        url = f"{SWAP_URL}/quote"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,  # Amount in smallest units (wei for ETH, 6 decimals for USDT)
            "includeGas": True
        }
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            time.sleep(1)  # Rate limit to avoid API errors
            print("here1")
            print(response)
            data = response.json()
            return float(data["dstAmount"]) / 1e18  # Convert from wei
        except Exception as e:
            print(f"Error fetching swap quote from {from_token} to {to_token}: {e}")
            return None

    def update_prices(self):
        """Updates the graph with real-time token exchange rates from 1inch."""
        print("🔄 Updating token prices...")
        for (from_token, from_token_address, to_token, to_token_address) in self.token_pairs:
            if from_token != to_token:
                print(f"Fetching price from {from_token} to {to_token}")
                price = self.get_swap_quote(from_token_address, to_token_address)
                if price:
                    if from_token not in self.graph:
                        self.graph[from_token] = {}
                    self.graph[from_token][to_token] = price
        return self.graph

if __name__ == "__main__":
    fetcher = PriceFetcher()

    # Test fetching available tokens
    print("✅ Available Tokens Number:", len(fetcher.get_available_tokens()))

    # Test fetching available liquidity sources
    print("✅ Liquidity Sources Number:", len(fetcher.get_liquidity_sources()))

    while True:
        graph = fetcher.update_prices()
        print(json.dumps(graph, indent=2))  # Print graph for debugging
        time.sleep(10)  # Refresh every 10 seconds