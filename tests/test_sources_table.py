
from facts_manager import FactsManager
from competitive_analysis import CompetitiveAnalysisEngine
import pandas as pd

# 1. Setup
print("🛠️ Setting up Facts Manager...")
mgr = FactsManager()
mgr.clear_all_facts() # Start fresh
mgr.generate_competitive_seed_data() # Inject seed

# 2. Instantiate Engine
print("🧠 Instantiating Competitive Engine...")
engine = CompetitiveAnalysisEngine(mgr)

# 3. Test Sources Table
print("\n--- Testing Sources Table Extraction ---")
sources_df = engine.get_sources_dataframe()

print(f"Rows: {len(sources_df)}")
print(f"Columns: {list(sources_df.columns)}")
print("\nFirst 5 rows:")
print(sources_df.head().to_string())

# Check required columns
required_cols = ["Variable / Fact", "Valeur", "Source", "Type Source", "Méthode", "Confiance"]
missing = [c for c in required_cols if c not in sources_df.columns]
if not missing:
    print("\n✅ All required columns are present.")
else:
    print(f"\n❌ Missing columns: {missing}")
