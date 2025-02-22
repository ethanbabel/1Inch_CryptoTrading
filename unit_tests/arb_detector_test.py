import unittest
import math
from arb_detector import ArbitrageDetector

class TestArbitrageDetector(unittest.TestCase):

    def setUp(self):
        """Set up sample graphs for testing."""
        self.graph_no_arbitrage = {
            "USDT": {"ETH": 0.0005, "DAI": 1.0},
            "ETH": {"DAI": 2000, "USDT": 1999},
            "DAI": {"USDT": 0.999, "ETH": 0.000401}
        }
        
        self.graph_with_arbitrage = {
            "USDT": {"ETH": 0.0005, "DAI": 1.0},
            "ETH": {"DAI": 2000, "USDT": 2100},  # Arbitrage exists here!
            "DAI": {"USDT": 1.01, "ETH": 0.000501}
        }

        self.single_token_graph = {
            "USDT": {}  # No paths
        }

        self.disconnected_graph = {
            "USDT": {"ETH": 0.0005},
            "ETH": {"DAI": 2000},
            "DAI": {"BTC": 0.01},  # BTC is disconnected from USDT
            "BTC": {}
        }

    def test_transform_graph(self):
        """Test if exchange rates are correctly transformed into negative logs."""
        detector = ArbitrageDetector(self.graph_no_arbitrage)
        transformed = detector.transform_graph()

        for token in self.graph_no_arbitrage:
            for neighbor, rate in self.graph_no_arbitrage[token].items():
                expected = -math.log(rate)
                self.assertAlmostEqual(transformed[token][neighbor], expected, places=5)

    def test_no_arbitrage(self):
        """Test that no arbitrage is detected when there is none."""
        detector = ArbitrageDetector(self.graph_no_arbitrage)
        self.assertEqual(detector.detect_arbitrage(), [])

    def test_detect_arbitrage(self):
        """Test that arbitrage is detected correctly."""
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        opportunities = detector.detect_arbitrage()
        self.assertGreater(len(opportunities), 0, "Arbitrage should be detected")
        for opportunity in opportunities:
            self.assertGreater(opportunity["profit_percentage"], 0, "Profit should be positive")
            self.assertEqual(opportunity["path"][0], opportunity["path"][-1], "Path should be cyclic")

    def test_extract_arbitrage_cycle(self):
        """Test if the arbitrage cycle extraction is correct."""
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        opportunities = detector.detect_arbitrage()
        for opportunity in opportunities:
            self.assertTrue("USDT" in opportunity["path"], "USDT should be part of the cycle")
            self.assertEqual(opportunity["path"][0], opportunity["path"][-1], "Cycle should start and end at the same token")

    def test_exchange_rate_calculations(self):
        """Test if the exchange rate calculations within cycles are correct."""
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        opportunities = detector.detect_arbitrage()
        for opportunity in opportunities:
            initial_value = 1.0
            final_value = 1.0
            for _, _, rate in opportunity["exchange_rates"]:
                final_value *= rate
            expected_profit_percentage = ((final_value - initial_value) / initial_value) * 100
            self.assertAlmostEqual(opportunity["profit_percentage"], expected_profit_percentage, places=5)

    def test_single_token(self):
        """Test handling of a graph with only one token."""
        detector = ArbitrageDetector(self.single_token_graph)
        self.assertEqual(detector.detect_arbitrage(), [], "Should return empty list for single-token graph")

    def test_disconnected_graph(self):
        """Test handling of a disconnected graph."""
        detector = ArbitrageDetector(self.disconnected_graph)
        self.assertEqual(detector.detect_arbitrage(), [], "Should return empty list since BTC is disconnected")

    def test_large_graph(self):
        """Test detection with a large graph of many tokens."""
        large_graph = {
            "USDT": {"ETH": 0.0004, "DAI": 1.0, "BTC": 0.000022},
            "ETH": {"DAI": 2000, "USDT": 1999, "BTC": 0.05},
            "DAI": {"USDT": 0.999, "ETH": 0.000401, "BTC": 0.000022},
            "BTC": {"USDT": 45000, "ETH": 20, "DAI": 22000}
        }
        detector = ArbitrageDetector(large_graph)
        self.assertEqual(detector.detect_arbitrage(), [], "Should return empty list if no arbitrage exists")

    def test_arbitrage_with_large_graph(self):
        """Test arbitrage detection in a large graph where arbitrage exists."""
        large_graph = {
            "USDT": {"ETH": 0.0005, "DAI": 1.0, "BTC": 0.000022},
            "ETH": {"DAI": 2000, "USDT": 2100, "BTC": 0.05},  # Arbitrage USDT → ETH → USDT
            "DAI": {"USDT": 1.01, "ETH": 0.000501, "BTC": 0.000044},
            "BTC": {"USDT": 45000, "ETH": 20, "DAI": 22000}
        }
        detector = ArbitrageDetector(large_graph)
        opportunities = detector.detect_arbitrage()
        self.assertGreater(len(opportunities), 0, "Arbitrage should be detected")

    def test_log_arbitrage_opportunity(self):
        """Test that the logging function runs without errors."""
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        opportunities = detector.detect_arbitrage()
        for opportunity in opportunities:
            try:
                detector.log_arbitrage_opportunity(opportunity)
            except Exception as e:
                self.fail(f"Logging function raised an error: {e}")

if __name__ == "__main__":
    unittest.main()
