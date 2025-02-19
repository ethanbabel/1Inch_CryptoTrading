import math
from price_fetcher import PriceFetcher
from ses import send_email
import datetime

class ArbitrageDetector:
    def __init__(self, graph):
        """Initialize the detector with a token exchange rate graph."""
        self.graph = graph
        self.emails = ["babelethan@gmail.com"]
        self.tokens = list(graph.keys())
        self.log_file = "arbitrage_log.txt"  # Define the log file name

    def transform_graph(self):
        """Transforms exchange rates into negative log weights for Bellman-Ford."""
        log_graph = {token: {} for token in self.tokens}
        for token in self.tokens:
            for neighbor, rate in self.graph[token].items():
                log_graph[token][neighbor] = -math.log(rate)
        return log_graph

    def bellman_ford_all_cycles(self, start_token):
        """Runs Bellman-Ford once and detects all unique arbitrage cycles efficiently."""
        transformed_graph = self.transform_graph()
        n = len(self.tokens)
        distances = {token: float("inf") for token in self.tokens}
        predecessors = {token: None for token in self.tokens}
        distances[start_token] = 0

        # Relax edges (n-1) times
        for _ in range(n - 1):
            for token in self.tokens:
                for neighbor in transformed_graph[token]:
                    if distances[token] + transformed_graph[token][neighbor] < distances[neighbor]:
                        distances[neighbor] = distances[token] + transformed_graph[token][neighbor]
                        predecessors[neighbor] = token

        # Find all unique negative cycles
        negative_cycles = []
        visited_cycles = set()
        
        for token in self.tokens:
            for neighbor in transformed_graph[token]:
                if distances[token] + transformed_graph[token][neighbor] < distances[neighbor]:
                    cycle = self.extract_arbitrage_cycle(predecessors, neighbor)
                    if cycle and tuple(cycle) not in visited_cycles:
                        visited_cycles.add(tuple(cycle))
                        negative_cycles.append(cycle)

        return negative_cycles

    def extract_arbitrage_cycle(self, predecessors, start):
        """Extracts an arbitrage cycle from the Bellman-Ford results."""
        cycle = []
        visited = set()
        while start not in visited:
            visited.add(start)
            start = predecessors[start]
        cycle_start = start
        while True:
            cycle.append(start)
            start = predecessors[start]
            if start == cycle_start:
                break
        cycle.append(cycle_start)
        cycle.reverse()
        return cycle

    def detect_arbitrage(self):
        """Detects all arbitrage opportunities in a single Bellman-Ford pass."""
        if not self.tokens:
            return []

        start_token = self.tokens[0]  # Pick any token as starting node
        detected_cycles = self.bellman_ford_all_cycles(start_token)
        
        arbitrage_opportunities = []
        for cycle in detected_cycles:
            opportunity = self.get_arbitrage_details(cycle)
            if opportunity:
                arbitrage_opportunities.append(opportunity)

        return arbitrage_opportunities

    def get_arbitrage_details(self, cycle):
        """Calculates exchange rates and profit percentage for an arbitrage cycle."""
        initial_value = 1.0  # Assume starting with 1 unit of the base token
        final_value = 1.0
        exchange_rates = []

        for i in range(len(cycle) - 1):
            from_token, to_token = cycle[i], cycle[i + 1]
            rate = self.graph[from_token][to_token]
            exchange_rates.append((from_token, to_token, rate))
            final_value *= rate

        profit_percentage = ((final_value - initial_value) / initial_value) * 100

        return {
            "path": cycle,
            "exchange_rates": exchange_rates,
            "profit_percentage": profit_percentage
        }

    def log_arbitrage_opportunity(self, opportunity):
        """Logs detected arbitrage opportunities in a structured format to both console and a file."""
        if not opportunity:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n🚀 {timestamp} - Arbitrage Opportunity Found!\n"
        log_entry += f"🔁 Path: {' → '.join(opportunity['path'])}\n"
        log_entry += "💱 Exchange Rates:\n"
        for from_token, to_token, rate in opportunity["exchange_rates"]:
            log_entry += f"    {from_token} → {to_token}: {rate:.6f}\n"
        log_entry += f"📈 Profit: {opportunity['profit_percentage']:.2f}%\n"
        log_entry += "-" * 50  # Separator for readability

        # Print to console
        print(log_entry)

        # Append to file
        with open(self.log_file, "a") as file:
            file.write(log_entry + "\n")

    def notify_arbitrage(self, opportunity):
        """Sends an email notification when an arbitrage opportunity is found."""
        email_body = f"""
        🚀 Arbitrage Opportunity Found!
        🔁 Path: {' → '.join(opportunity['path'])}
        
        💱 Exchange Rates:
        {''.join([f"{from_token} → {to_token}: {rate:.6f}\n" for from_token, to_token, rate in opportunity["exchange_rates"]])}
        
        📈 Profit: {opportunity['profit_percentage']:.2f}%
        """
        send_email(self.emails, "Arbitrage Opportunity Detected!", email_body)