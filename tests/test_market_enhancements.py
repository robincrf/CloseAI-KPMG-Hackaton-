
from facts_manager import FactsManager
from market_estimation_engine import MarketEstimationEngine
import pandas as pd

# 1. Setup
print("🛠️ Setting up Facts Manager...")
mgr = FactsManager()
mgr.clear_all_facts() 

# Inject some facts with "approximate" keys to test Fuzzy Logic
mgr.add_or_update_fact({"key": "target_audience", "value": 1000, "category": "market_estimation"})
mgr.add_or_update_fact({"key": "subscription_fee", "value": 50, "category": "market_estimation"})
# Inject standard keys for others
mgr.add_or_update_fact({"key": "sam_percent", "value": 0.5, "category": "market_estimation"})

print("✅ Facts injected.")

# 2. Instantiate Engine
engine = MarketEstimationEngine(mgr)

# 3. Test Fuzzy Logic
print("\n--- Testing Fuzzy Logic ---")
print("Target: 'total_potential_customers' (expecting match with 'target_audience')")
val, _, _ = engine._get_fact_val_and_meta("total_potential_customers")
print(f"Result: {val} (Should be 1000)")

print("Target: 'average_price' (expecting match with 'subscription_fee')")
val2, _, _ = engine._get_fact_val_and_meta("average_price")
print(f"Result: {val2} (Should be 50)")

if val == 1000 and val2 == 50:
    print("✅ Fuzzy Logic Passed.")
else:
    print("❌ Fuzzy Logic Failed.")

# 4. Test Sensitivity Analysis
print("\n--- Testing Sensitivity Analysis ---")
import math
# Base Calculation
base_res = engine.get_demand_estimation()
print(f"Base Value: {base_res.estimated_value}") # 1000 * 50 = 50000

# Apply Override (+10% Price)
overrides = {"average_price": 1.10}
sens_res = engine.get_demand_estimation(overrides)
print(f"Sens Value (+10% Price): {sens_res.estimated_value}") # 55000

if math.isclose(sens_res.estimated_value, 55000.0, rel_tol=1e-5):
    print("✅ Sensitivity Analysis Passed.")
else:
    print("❌ Sensitivity Analysis Failed.")

# 5. Test Waterfall Data
print("\n--- Testing Waterfall Data ---")
wf_df = engine.get_waterfall_data(base_tam=100000)
print(wf_df.to_string())

if "Total Addressable Market (TAM)" in wf_df["x"].values and "Revenus Potentiels" in wf_df["x"].values:
    print("✅ Waterfall Structure Valid.")
else:
    print("❌ Waterfall Structure Invalid.")
