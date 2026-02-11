
import sys
import os

# Mock FactsManager
class MockFactsManager:
    def __init__(self, facts):
        self.facts = facts

    def get_all_keys(self):
        return [f["key"] for f in self.facts]

    def get_facts(self, key):
        return [f for f in self.facts if f["key"] == key]

# Define test facts
facts = [
    # Macro
    {"key": "tam_global_market", "value": 10_000_000_000.0, "confidence": "high", "source_type": "Report"},
    {"key": "sam_percent", "value": 0.20, "confidence": "medium", "source_type": "Estimation"},
    {"key": "som_share", "value": 0.05, "confidence": "low", "source_type": "Estimation"},
    
    # Demand
    {"key": "total_potential_customers", "value": 5000.0, "confidence": "high", "source_type": "CRM"},
    {"key": "average_price", "value": 12000.0, "confidence": "high", "source_type": "Sales"},
    
    # Segmented Pricing
    {"key": "price_core", "value": 10000.0, "confidence": "high", "source_type": "Pricing"},
    {"key": "price_modules", "value": 5000.0, "confidence": "medium", "source_type": "Pricing"},
    {"key": "price_services", "value": 3000.0, "confidence": "high", "source_type": "Pricing"},
    
    # Reality Factor Inputs
    {"key": "sales_cycle_months", "value": 9.0, "confidence": "high", "source_type": "Sales"}, # Should trigger 0.9 friction
    {"key": "competitor_count", "value": ["CompA"] * 60, "confidence": "high", "source_type": "Market Scan"}, # List of 60 items, Should trigger 0.9 friction
    
    # Supply
    {"key": "top_players_cumulative_revenue", "value": 100_000_000.0, "confidence": "medium", "source_type": "Financials"},
    {"key": "top_players_market_share", "value": 0.50, "confidence": "low", "source_type": "Guess"},
    {"key": "market_fragmentation_index", "value": 1.5, "confidence": "low", "source_type": "Proxy"},
]

from market_estimation_engine import MarketEstimationEngine

def test_engine():
    mgr = MockFactsManager(facts)
    engine = MarketEstimationEngine(mgr)
    
    print("--- Running Estimations ---")
    comps = engine.get_all_estimations()
    
    for c in comps:
        print(f"\nComponent: {c.name}")
        print(f"Value: {c.estimated_value:,.0f} €" if c.estimated_value else "Value: None")
        print(f"Strategy: {c.selected_strategy_name}")
        print(f"Reality Score: {c.reality_score}")
        print(f"Narrative: {c.strategic_narrative}")
        print(f"Breakdown: {c.calculation_breakdown}")

    # Check Specific Logic
    
    # 1. Segmented Pricing
    demand_comp = comps[1]
    assert demand_comp.selected_strategy_name == "Pricing Segmenté (Core + Services + Upsell)", "Segmented Pricing should be selected"
    # Expected: 5000 * (10000+5000+3000) = 5000 * 18000 = 90,000,000
    # Friction: 
    # Sales Cycle (9m) -> 0.9
    # Competitor (>50) -> 0.9
    # Total Friction = 0.81
    # Final = 90M * 0.81 = 72,900,000
    
    val = demand_comp.estimated_value
    print(f"\nDemand Value Check: {val}")
    
    # 2. Strategic Summary
    tam = comps[0].estimated_value
    som = demand_comp.estimated_value
    summary = engine.generate_strategic_summary_text(tam, som)
    print(f"\nStrategic Summary: {summary}")
    
    # 3. Waterfall
    wf = engine.get_waterfall_data(tam)
    print("\nWaterfall Data Head:")
    print(wf.head())

if __name__ == "__main__":
    test_engine()
