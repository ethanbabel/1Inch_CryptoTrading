from arb_detector import ArbitrageDetector

# Test Notify Arbitrage
graph_with_arbitrage = {
    "USDT": {"ETH": 0.0005, "DAI": 1.0},
    "ETH": {"DAI": 2000, "USDT": 2100},  # Arbitrage exists here!
    "DAI": {"USDT": 1.01, "ETH": 0.000501}
}
detector = ArbitrageDetector(graph_with_arbitrage)
opportunities = detector.detect_arbitrage()
for opportunity in opportunities:
    detector.log_arbitrage_opportunity(opportunity)
    detector.notify_arbitrage(opportunity)
print("Notification sent, check your email!")