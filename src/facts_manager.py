
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

class FactsManager:
    """
    Manages a collection of 'Facts' for the Facts-First architecture.
    A Fact is a standardized unit of information:
    {
        "id": "unique_id",
        "category": "market_estimation | competition | etc.",
        "key": "tam_value",
        "value": 1000000,
        "unit": "USD",
        "source": "Gartner 2024",
        "as_of": "2024-01-01",
        "confidence": "high",
        "notes": "Estimated based on..."
    }
    """
    
    def __init__(self, json_path: str = None):
        if json_path is None:
            # Robustly locate data directory relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, "data", "market_sizing_facts.json")
            
        self.json_path = json_path
        self._load_facts()

    def _load_facts(self):
        """Loads facts from the JSON file, or initializes an empty list if not found."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.facts = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding {self.json_path}. Starting with empty facts.")
                self.facts = []
        else:
            self.facts = []

    def clear_all_facts(self):
        """Clears all facts from memory and disk. Used for session reset."""
        self.facts = []
        self.save_facts()
        print("🗑️ Facts Manager: All facts cleared.")

    def save_facts(self):
        """Saves current facts to the JSON file."""
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.facts, f, indent=4, ensure_ascii=False)

    def get_facts(self, category: Optional[str] = None, key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves facts filtered by category and/or key."""
        filtered = self.facts
        if category:
            filtered = [f for f in filtered if f.get("category") == category]
        if key:
            filtered = [f for f in filtered if f.get("key") == key]
        return filtered
        
    def get_all_keys(self) -> List[str]:
        """Returns a list of all unique keys in the facts database."""
        return list(set([f.get("key") for f in self.facts if f.get("key")]))

    def get_fact_value(self, key: str, default: Any = None) -> Any:
        """Helper to get a single fact value by key."""
        facts = self.get_facts(key=key)
        if facts:
            return facts[0].get("value", default)
        return default

    def add_or_update_fact(self, fact: Dict[str, Any]):
        """Adds a new fact or updates an existing one based on 'key' (or 'id')."""
        # Simple update strategy: match by key for single-value facts
        # Ideally should use ID, but for this mockup, Key is easier
        
        existing_index = -1
        for i, f in enumerate(self.facts):
            if f.get("key") == fact.get("key") and f.get("category") == fact.get("category"):
                existing_index = i
                break
        
        if existing_index >= 0:
            self.facts[existing_index].update(fact)
        else:
            if "id" not in fact:
                fact["id"] = f"fact_{len(self.facts)}_{int(datetime.now().timestamp())}"
            self.facts.append(fact)
        
        self.save_facts()

    def calculate_estimation_level(self) -> Dict[str, Any]:
        """
        Determines the estimation level (0-3) based on available facts.
        
        Logic:
        - Level 0 (Structural): TAM is missing.
        - Level 1 (Top-Down): TAM + SAM% + SOM% are present.
        - Level 2 (Bottom-Up): Potential Customers + Price/ARPU are present.
        - Level 3 (Triangulation): Level 1 AND Level 2 are valid.
        
        Returns:
            Dict with keys: 'level', 'confidence_score', 'explanation', 'method'
        """
        # Fetch Top-Down facts
        tam = self.get_fact_value("tam_global_market")
        sam_pct = self.get_fact_value("sam_percent")
        som_pct = self.get_fact_value("som_share")
        
        # Fetch Bottom-Up facts
        customers = self.get_fact_value("total_potential_customers")
        price = self.get_fact_value("average_price")
        
        # Determine validity of methods
        has_top_down = (tam is not None and tam > 0) and (sam_pct is not None) and (som_pct is not None)
        has_bottom_up = (customers is not None and customers > 0) and (price is not None and price > 0)
        
        level = 0
        confidence = 0.0
        method = "None"
        explanation = "Données insuffisantes pour une estimation. (TAM manquant)"

        if has_top_down and has_bottom_up:
            level = 3
            confidence = 0.85
            method = "Triangulation"
            explanation = "Estimation robuste basée sur la convergence Top-Down et Bottom-Up."
        elif has_bottom_up:
            level = 2
            confidence = 0.60
            method = "Bottom-Up"
            explanation = "Estimation basée sur les volumes (Clients x Prix). Manque la vision globale (TAM)."
        elif has_top_down:
            level = 1
            confidence = 0.40
            method = "Top-Down"
            explanation = "Estimation théorique basée sur la taille du marché global (TAM). Nécessite une validation terrain."
        else:
            # Level 0 Check specifics
            if tam is None:
                explanation = "TAM manquant. Structure d'estimation affichée uniquement."
            else:
                explanation = "Données partielles. Complétez les pourcentages SAM/SOM ou les données Clients/Prix."

        return {
            "level": level,
            "confidence_score": confidence,
            "explanation": explanation,
            "method": method
        }

    def get_all_facts_as_dataframe(self) -> pd.DataFrame:
        """Returns all facts as a Pandas DataFrame for easy viewing."""
        if not self.facts:
            return pd.DataFrame()
        return pd.DataFrame(self.facts)


    def get_market_scope(self) -> str:
        """Retrieves the current market scope definition."""
        return self.get_fact_value("market_scope", "Marché non défini")

    def set_market_scope(self, scope_text: str):
        """Updates the market scope definition."""
        self.add_or_update_fact({
            "id": "ctx_market_scope",
            "category": "context",
            "key": "market_scope",
            "value": scope_text,
            "unit": "text",
            "source": "User Input",
            "confidence": "high",
            "notes": "Définition du périmètre de l'analyse"
        })

    def generate_seed_data(self):
        """Generates seed data if facts are empty."""
        if self.facts:
            return

        seed_facts = [
            # CONTEXT
            {
                "id": "ctx_market_scope",
                "category": "context",
                "key": "market_scope",
                "value": "Logiciels de Gestion (ERP/CRM) pour PME en France",
                "unit": "text",
                "source": "User Input",
                "confidence": "high",
                "notes": "Définition du périmètre de l'analyse"
            },
            # MARKET SIZING - TOP DOWN
            {
                "id": "md_tam_global",
                "category": "market_estimation",
                "key": "tam_global_market",
                "value": 5000000000,
                "unit": "EUR",
                "source": "Gartner 2023",
                "source_type": "Secondaire (Rapport)",
                "retrieval_method": "Direct",
                "confidence": "high",
                "notes": "Marché global des logiciels de gestion"
            },
            {
                "id": "md_sam_segment",
                "category": "market_estimation",
                "key": "sam_percent",
                "value": 0.20,
                "unit": "%",
                "source": "Hypothèse Interne",
                "source_type": "Interne",
                "retrieval_method": "Estimation",
                "confidence": "medium",
                "notes": "Focus sur le segment PME en Europe"
            },
            {
                "id": "md_som_share",
                "category": "market_estimation",
                "key": "som_share",
                "value": 0.05,
                "unit": "%",
                "source": "Plan Stratégique 2025",
                "source_type": "Interne",
                "retrieval_method": "Cible Stratégique",
                "confidence": "low",
                "notes": "Part de marché cible à 3 ans"
            },
            
            # MARKET SIZING - BOTTOM UP (Partial data for placeholder demo)
            {
                "id": "bu_customers",
                "category": "market_estimation",
                "key": "total_potential_customers",
                "value": 15000,
                "unit": "companies",
                "source": "INSEE",
                "source_type": "Primaire (Base Publique)",
                "retrieval_method": "Extraction",
                "confidence": "high",
                "notes": "Nombre d'entreprises > 50 salariés"
            },
             {
                "id": "bu_price",
                "category": "market_estimation",
                "key": "average_price",
                "value": None, # MISSING VALUE DEMO
                "unit": "EUR/year",
                "source": "TBD",
                "source_type": "Manquant",
                "retrieval_method": "TBD",
                "confidence": "low",
                "notes": "Prix moyen manquant"
            },

            # COMPETITION
            {
                "id": "comp_1",
                "category": "competition",
                "key": "competitor_list",
                "value": ["Competitor A", "Competitor B", "Competitor C"],
                "unit": "list",
                "source": "Manual",
                "source_type": "Interne",
                "retrieval_method": "Saisi manuel",
                "confidence": "high",
                "notes": ""
            },
            {
                "id": "comp_1_revenue",
                "category": "competition",
                "key": "competitor_a_revenue",
                "value": 50000000,
                "unit": "EUR",
                "source": "Annual Report 2022",
                "source_type": "Publique (Rapport Financier)",
                "retrieval_method": "Direct",
                "confidence": "high",
                "notes": ""
            },
            
            # MARKET SIZING - SUPPLY (Production)
            {
                "id": "sup_production",
                "category": "market_estimation",
                "key": "production_volume",
                "value": None, # Missing for demo
                "unit": "units/year",
                "source": "Industry Report",
                "source_type": "Secondaire",
                "retrieval_method": "Proxy Sectoriel",
                "confidence": "low",
                "notes": "Volume de production local ou importé"
            },
            {
                "id": "sup_unit_val",
                "category": "market_estimation",
                "key": "average_unit_market_value",
                "value": None,
                "unit": "EUR",
                "source": "Market Analysis",
                "source_type": "Secondaire",
                "retrieval_method": "Benchmark",
                "confidence": "low",
                "notes": "Valeur marchande par unité produite"
            }
        ]
        self.facts = seed_facts
        self.save_facts()

    def ingest_financial_facts(self, ticker: str):
        """
        Fetches financial data from facts_service and stores it as Facts.
        """
        # Lazy import to avoid circular dependency
        from facts_service import facts_service
        
        print(f"🔄 Ingesting financials for {ticker}...")
        try:
            data = facts_service.get_company_facts(ticker)
            if data.get("error"):
                print(f"❌ Error fetching financials: {data['error']}")
                return

            info = data.get("info", {})
            derived = data.get("derived", {})
            currency = info.get("currency", "USD")
            date_str = datetime.now().strftime('%Y-%m-%d')
            source_label = f"Yahoo Finance ({date_str})"

            # Helper to add fact
            def add_f(key, val, unit, category="financials", notes=""):
                if val is not None:
                    # Ensure value is JSON serializable (convert numpy types)
                    if hasattr(val, "item"): val = val.item()
                    
                    self.add_or_update_fact({
                        "id": f"yf_{ticker}_{key}",
                        "category": category,
                        "key": key,
                        "value": val,
                        "unit": unit,
                        "source": source_label,
                        "confidence": "high",
                        "notes": notes
                    })

            # 1. Revenus (Last Year)
            rev_series = derived.get("revenue")
            if rev_series is not None and not rev_series.empty:
                 last_dt = rev_series.index[-1]
                 add_f("last_revenue", rev_series.iloc[-1], currency, notes=f"Fiscal Year: {last_dt.year}")

            # 2. Net Income
            inc_series = derived.get("net_income")
            if inc_series is not None and not inc_series.empty:
                 add_f("last_net_income", inc_series.iloc[-1], currency)

            # 3. Employees
            if "fullTimeEmployees" in info:
                add_f("employees", info["fullTimeEmployees"], "people", notes="Full Time Employees")

            # 4. Market Cap
            if "marketCap" in info:
                add_f("market_cap", info["marketCap"], currency)
            
            # 5. Marges
            margin_series = derived.get("net_margin")
            if margin_series is not None and not margin_series.empty:
                add_f("net_margin_percent", margin_series.iloc[-1], "%")

            print(f"✅ Ingested financial facts for {ticker}")

        except Exception as e:
            print(f"❌ Error ingesting financial facts: {e}")
            import traceback
            traceback.print_exc()

    def ingest_strategic_facts(self, company: str, ticker: str = None):
        """
        Fetches strategic analysis from strategic_facts_service (Mistral) and stores it.
        """
        from strategic_facts_service import strategic_facts_service
        
        print(f"🔄 Ingesting strategic analysis for {company}...")
        try:
            # Force refresh to ensure we get a new generation if needed, or use cache inside service
            analysis = strategic_facts_service.get_strategic_analysis(company, ticker, force_refresh=False)
            
            if analysis.get("error"):
                print(f"❌ Error fetching strategic facts: {analysis['error']}")
                return

            source_label = "Mistral AI Analysis"
            
            # Store SWOT
            if "swot" in analysis:
                self.add_or_update_fact({
                    "id": f"strat_swot_{company}",
                    "category": "strategic_analysis",
                    "key": "swot_data",
                    "value": analysis["swot"],
                    "unit": "json",
                    "source": source_label,
                    "confidence": "medium",
                    "notes": "Generated SWOT Analysis"
                })

            # Store BCG
            if "bcg" in analysis:
                self.add_or_update_fact({
                    "id": f"strat_bcg_{company}",
                    "category": "strategic_analysis",
                    "key": "bcg_data",
                    "value": analysis["bcg"],
                    "unit": "json",
                    "source": source_label,
                    "confidence": "medium",
                    "notes": "Generated BCG Matrix Data"
                })

            # Store PESTEL
            if "pestel" in analysis:
                self.add_or_update_fact({
                    "id": f"strat_pestel_{company}",
                    "category": "strategic_analysis",
                    "key": "pestel_data",
                    "value": analysis["pestel"],
                    "unit": "json",
                    "source": source_label,
                    "confidence": "medium",
                    "notes": "Generated PESTEL Analysis"
                })

            print(f"✅ Ingested strategic facts for {company}")

        except Exception as e:
            print(f"❌ Error ingesting strategic facts: {e}")
            import traceback
            traceback.print_exc()

    def generate_competitive_seed_data(self):
        """
        Generates seed facts specifically for the Competitive Analysis Module demo.
        Only runs if no competitive facts exist.
        """
        # Check if already populated
        existing = self.get_fact_value("competitor_list")
        if existing and len(existing) > 0:
            # OPTIONAL: Clear and regenerate if you want to force update sources
            # But for now we respect existing data. 
            # To force update for the user, we might need them to clear session or we force overwrite here.
            # Let's force update the fields that might be missing sources.
            pass

        print("🚦 Generating Competitive Seed Data for Demo (Enriched Sources)...")
        
        # 0. The Actors
        competitors = ["NexusCorp", "AgileFlow", "OldSchool Inc", "BudgetSoft"]
        self.add_or_update_fact({
            "key": "competitor_list", 
            "value": competitors, 
            "category": "competition",
            "source": "KPMG Competitive Landscape Report 2024",
            "source_type": "Interne",
            "confidence": "High"
        })
        
        # 1. Actors Metadata (Block 1)
        meta = [
            ("NexusCorp", "Leader", "Global", "500M", "Annual Report 2023"),
            ("AgileFlow", "Challenger", "Europe", "50M", "Crunchbase"),
            ("OldSchool Inc", "Incumbent", "Global", "1.2B", "Annual Report 2023"),
            ("BudgetSoft", "Niche (Low Cost)", "Asia", "10M", "Company Website")
        ]
        for name, typ, geo, rev, src in meta:
            self.add_or_update_fact({"key": f"comp_{name}_type", "value": typ, "category": "competition", "source": "Analyste KPMG", "confidence": "High"})
            self.add_or_update_fact({"key": f"comp_{name}_geo", "value": geo, "category": "competition", "source": src, "confidence": "High"})
            self.add_or_update_fact({"key": f"comp_{name}_revenue", "value": rev, "category": "competition", "source": src, "confidence": "High"})

        # 2. Offerings (Block 2)
        features = ["Cloud Native", "AI Features", "24/7 Support", "Custom API"]
        self.add_or_update_fact({"key": "market_key_features", "value": features, "category": "competition", "source": "Market Study Q1", "confidence": "High"})
        
        # Assign random feature capabilities
        # Nexus: All Yes
        for f in features: 
            self.add_or_update_fact({
                "key": f"comp_NexusCorp_feat_{f.lower().replace(' ', '_')}", 
                "value": "✅ Yes", "category": "competition", 
                "source": "NexusCorp Feature Page",
                "confidence": "High"
            })
        
        # BudgetSoft: All No except API
        for f in features: 
            val = "❌ No" if "API" not in f else "✅ Yes"
            self.add_or_update_fact({"key": f"comp_BudgetSoft_feat_{f.lower().replace(' ', '_')}", 
                                     "value": val, "category": "competition",
                                     "source": "G2 Crowd Reviews",
                                     "confidence": "Medium"
                                     })
            
        # Others mixed
        self.add_or_update_fact({"key": "comp_AgileFlow_feat_cloud_native", "value": "✅ Yes", "category": "competition", "source": "AgileFlow Doc", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_AgileFlow_feat_ai_features", "value": "🚧 Beta", "category": "competition", "source": "Press Release Jan 2025", "confidence": "Medium"})
        self.add_or_update_fact({"key": "comp_AgileFlow_feat_24/7_support", "value": "❌ No", "category": "competition", "source": "Service Terms", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_AgileFlow_feat_custom_api", "value": "✅ Yes", "category": "competition", "source": "Developer Portal", "confidence": "High"})

        self.add_or_update_fact({"key": "comp_OldSchool Inc_feat_cloud_native", "value": "❌ No", "category": "competition", "source": "Tech Radar", "confidence": "Medium"})
        self.add_or_update_fact({"key": "comp_OldSchool Inc_feat_ai_features", "value": "❌ No", "category": "competition", "source": "Tech Radar", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_OldSchool Inc_feat_24/7_support", "value": "✅ Yes", "category": "competition", "source": "Client Contract Template", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_OldSchool Inc_feat_custom_api", "value": "❌ Legacy", "category": "competition", "source": "Developer Portal", "confidence": "High"})

        # 3. Differentiation Claims (Block 3)
        self.add_or_update_fact({"key": "comp_NexusCorp_claim", "value": "The All-in-One Enterprise Standard", "category": "competition", "source": "Homepage Hero", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_AgileFlow_claim", "value": "Move fast with AI-driven workflows", "category": "competition", "source": "LinkedIn Bio", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_OldSchool Inc_claim", "value": "Reliability you can trust since 1980", "category": "competition", "source": "About Us Page", "confidence": "High"})
        self.add_or_update_fact({"key": "comp_BudgetSoft_claim", "value": "Lowest price guaranteed", "category": "competition", "source": "Pricing Page", "confidence": "High"})

        # 4. Market Expectations (Block 4) -> "Market Voice"
        expectations = [
            {"criterion": "Real-time Collaboration", "importance": "High", "met": "Yes"},
            {"criterion": "Native AI Integration", "importance": "Critical", "met": "Partial"}, # Gap?
            {"criterion": "Deep Customization", "importance": "Medium", "met": "Yes"},
            {"criterion": "Transparent Pricing", "importance": "High", "met": "No"} # BIG Gap
        ]
        self.add_or_update_fact({"key": "market_expectations", "value": expectations, "category": "competition", "source": "Forrester Wave 2024", "confidence": "Medium"})
        
        self.save_facts()
        print("✅ Competitive Seed Data Ingested (Enriched).")

# Singleton instance
facts_manager = FactsManager()
# NO AUTOMATIC SEED - Facts must be generated dynamically per session
