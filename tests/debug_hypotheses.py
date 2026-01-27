
import os
import sys
from dotenv import load_dotenv

# Load env
load_dotenv()

try:
    import facts_manager
    from strategic_facts_service import strategic_facts_service
    from market_estimation_engine import MarketEstimationEngine
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_generation():
    print("--- Testing Strategic Facts Generation ---")
    
    # Check API Key
    key = os.getenv("MISTRAL_API_KEY")
    if not key:
        print("❌ MISTRAL_API_KEY not found in env.")
    else:
        print(f"✅ MISTRAL_API_KEY found (len={len(key)})")

    scope = "Logiciels CRM pour PME en France"
    
    print(f"Generating facts for scope: {scope}...")
    facts = strategic_facts_service.generate_market_sizing_facts(scope)
    
    print(f"Generated {len(facts)} facts.")
    
    if not facts:
        print("❌ No facts generated. Check LLM logs or API limits.")
        return

    # Ingest
    print("Ingesting facts...")
    for f in facts:
        print(f" - Adding {f['key']}: {f['value']}")
        facts_manager.facts_manager.add_or_update_fact(f)
        
    # Check Manager
    print(f"Facts in Manager: {len(facts_manager.facts_manager.facts)}")
    
    # Check Engine Output
    print("Checking Engine Table...")
    engine = MarketEstimationEngine(facts_manager.facts_manager)
    df = engine.get_consolidated_facts_table()
    
    print("DataFrame Shape:", df.shape)
    if not df.empty:
        print(df.head())
    else:
        print("❌ DataFrame is empty!")

if __name__ == "__main__":
    test_generation()
