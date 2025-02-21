import requests
import json
import time
import os
from dotenv import load_dotenv
import csv
import threading

load_dotenv()
ONEINCH_API_KEY = os.getenv("1INCH_API_KEY")

# 1inch API Configuration
CHAIN_ID = 1  # Ethereum Mainnet
BASE_URL = f"https://api.1inch.dev"
SWAP_URL = f"{BASE_URL}/swap/v6.0/{CHAIN_ID}"
HEADERS = {
    "Authorization": f"Bearer {ONEINCH_API_KEY}",
    "accept": "application/json"
}

TOKEN_DECIMALS = {
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": 6,  # USDT
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": 18, # WETH
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": 18, # LINK
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": 18, # DAI
    "0xb8c77482e45f1f44de1745f52c74426c631bdd52": 18, # BNB
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": 8,  # WBTC
}

class PriceFetcher:
    def __init__(self, token_pairs, throttler):
        self.graph = {}  # Adjacency list representation of token exchange rates
        self.token_pairs = token_pairs
        self.throttler = throttler
        
    def fetch_price(self, url, headers, params):
        """Fetch price while obeying the global rate limit."""
        self.throttler.enforce_rate_limit()  # Ensure we don’t exceed 1 req/sec
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 400:
            print(f"⚠️ API returned 400 (Bad Request) for {params['src']} → {params['dst']}")
            print(f"📜 Full Request URL: {response.url}")
            print(f"📜 Full Request Headers: {headers}")
            print(f"📜 Full Request Params: {params}")
            print(f"📜 API Response: {response.text}")
        
        # Log response for debugging
        if response.status_code != 200:
            print(f"⚠️ API returned {response.status_code} for {params.get('src', 'UNKNOWN')} → {params.get('dst', 'UNKNOWN')}")
            return None

        try:
            data = response.json()
            if not isinstance(data, dict):  # Ensure we only return dicts
                print(f"⚠️ Unexpected response format: {data}")
                return None
            return data  # Return full API response instead of extracting dstAmount here
        except Exception as e:
            print(f"❌ JSON decode error: {e} | Response: {response.text}")
            return None

    def get_token_price_in_usd(self, token_address):
        """Fetches the USD price of a given token, adjusting for different response formats."""
        url = f"https://api.1inch.dev/price/v1.1/1/{token_address.lower()}"
        params = {
            "tokens": token_address.lower(),
            "currency": "USD"
        } 

        headers = {
            "Authorization": f"Bearer {ONEINCH_API_KEY}",
            "accept": "application/json"
        }

        self.throttler.enforce_rate_limit()  # Ensure we don’t exceed 1 req/sec
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"⚠️ Failed to fetch USD price for {token_address}. Status: {response.status_code}")
            print(f"📜 Full Response: {response.text}")
            return None

        try:
            data = response.json()

            # If the price is directly mapped as a string, convert it to float
            if token_address.lower() in data:
                return float(data[token_address.lower()])
        
            print(f"⚠️ Token {token_address} not found in API response. Full data: {data}")
            return None

        except Exception as e:
            print(f"❌ JSON decode error: {e} | Response: {response.text}")
            return None

    def get_swap_quote(self, from_token, to_token, base_amount_usd=100):
        """Fetch the best swap price from 1inch API."""
        if not from_token or not to_token:
            print(f"⚠️ Invalid token pair: {from_token} → {to_token}")
            return None

        # Get the USD value of the source token
        price_in_usd = self.get_token_price_in_usd(from_token)
        if not price_in_usd:
            print(f"⚠️ Unable to determine USD value for {from_token}. Using default amount.")
            return None

        # Convert $100 worth of the token into smallest units
        amount_in_token = base_amount_usd / price_in_usd  # How much source token equals $100
        decimals = TOKEN_DECIMALS.get(from_token, 18)  # Default to 18 if not found
        amount = int(amount_in_token * (10 ** decimals))  # Convert to smallest unit
        
        url = f"{SWAP_URL}/quote"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,  # Amount in smallest units (wei for ETH, 6 decimals for USDT)
            "includeGas": True
        }
        try:
            data = self.fetch_price(url, HEADERS, params)
            if data and "dstAmount" in data:
                return float(data["dstAmount"]) / 1e18  # Convert from wei
            return None
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