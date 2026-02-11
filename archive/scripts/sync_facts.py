import sys
import os
import argparse

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facts_manager import facts_manager

def main():
    parser = argparse.ArgumentParser(description="Sync facts from YFinance and Mistral")
    parser.add_argument("--company", type=str, required=True, help="Company Name")
    parser.add_argument("--ticker", type=str, required=True, help="Ticker Symbol (e.g. AAPL)")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Sync for {args.company} ({args.ticker})...")
    
    # 1. Ingest Financials
    facts_manager.ingest_financial_facts(args.ticker)
    
    # 2. Ingest Strategic Analysis
    facts_manager.ingest_strategic_facts(args.company, args.ticker)
    
    # 3. Save (already handled by add_or_update_fact but good to confirm)
    facts_manager.save_facts()
    
    print("✅ Sync Complete. Facts saved to market_sizing_facts.json")

if __name__ == "__main__":
    main()
