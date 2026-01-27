from typing import List, Dict, Any, Optional
import pandas as pd
from facts_manager import FactsManager

class CompetitiveAnalysisEngine:
    """
    Engine for interpreting facts to produce a competitive analysis.
    Does NOT collect data. 
    Strictly interprets existing facts from FactsManager.
    """

    def __init__(self, facts_manager: FactsManager):
        self.mgr = facts_manager

    # -------------------------------------------------------------------------
    # Block 1: Actors Analysis
    # -------------------------------------------------------------------------
    def analyze_actors(self) -> Dict[str, Any]:
        """
        Block 1: Identifies and qualifies relevant actors.
        Output: List of actors with their calculated typology and similarity score.
        """
        competitors = self.mgr.get_fact_value("competitor_list", [])
        actors_data = []

        # Target Company Context
        target_scope = self.mgr.get_market_scope()
        
        for comp_name in competitors:
            # Fact Retrieval for each competitor
            f_type = self.mgr.get_fact_value(f"comp_{comp_name}_type", "Niche Player")
            f_rev = self.mgr.get_fact_value(f"comp_{comp_name}_revenue", "N/A")
            f_geo = self.mgr.get_fact_value(f"comp_{comp_name}_geo", "Global")
            
            # Simple Logic: typology based on manual fact or simple revenue heuristic if available
            typology = f_type
            
            actors_data.append({
                "Name": comp_name,
                "Typology": typology,
                "Geo": f_geo,
                "Revenue": f_rev
            })
            
        return {
            "actors_table": pd.DataFrame(actors_data),
            "summary_text": f"Identified {len(actors_data)} actors in the {target_scope} landscape."
        }

    # -------------------------------------------------------------------------
    # Block 2: Offerings Analysis
    # -------------------------------------------------------------------------
    def analyze_offerings(self) -> pd.DataFrame:
        """
        Block 2: Compares real offerings (features, service levels).
        Output: Matrix of [Actor x Key Feature].
        """
        competitors = self.mgr.get_fact_value("competitor_list", [])
        # Also include "Ma Société" (Target) if facts exist
        # For demo, we stick to competitors list + implicitly the target if we had one
        
        # Get list of key features/criteria defined in facts
        key_features = self.mgr.get_fact_value("market_key_features", ["Price", "Quality", "Support"])
        
        matrix_rows = []
        for comp in competitors:
            row = {"Actor": comp}
            for feat in key_features:
                # Try to find specific fact: comp_X_feat_Y
                # Key format: comp_{comp_name}_feat_{feat_name}
                clean_feat_key = feat.lower().replace(" ", "_")
                val = self.mgr.get_fact_value(f"comp_{comp}_feat_{clean_feat_key}", "Unknown")
                row[feat] = val
            matrix_rows.append(row)
            
        return pd.DataFrame(matrix_rows)

    # -------------------------------------------------------------------------
    # Block 3: Differentiation & Value Prop
    # -------------------------------------------------------------------------
    def analyze_differentiation(self) -> pd.DataFrame:
        """
        Block 3: Clusters actors by their claimed differentiation.
        """
        competitors = self.mgr.get_fact_value("competitor_list", [])
        diff_data = []
        
        for comp in competitors:
            claim = self.mgr.get_fact_value(f"comp_{comp}_claim", "Generalist")
            cluster = "Standard"
            
            # Simple keyword logic for clustering (mocking NLP)
            c_lower = claim.lower()
            if "cheap" in c_lower or "price" in c_lower or "cost" in c_lower:
                cluster = "Cost Leader"
            elif "quality" in c_lower or "premium" in c_lower or "best" in c_lower:
                cluster = "Premium"
            elif "inno" in c_lower or "tech" in c_lower or "ai" in c_lower:
                cluster = "Innovator"
            elif "service" in c_lower or "support" in c_lower:
                cluster = "Service-Centric"
                
            diff_data.append({
                "Actor": comp,
                "Claimed Value": claim,
                "Positioning Cluster": cluster
            })
            
        return pd.DataFrame(diff_data)

    # -------------------------------------------------------------------------
    # Block 4: Demand (Market Expectations)
    # -------------------------------------------------------------------------
    def analyze_demand(self) -> Dict[str, Any]:
        """
        Block 4: Synthesizes market expectations from facts.
        """
        expectations = self.mgr.get_fact_value("market_expectations", [])
        # Example structure of fact: [{"criterion": "Speed", "importance": "High", "met": False}]
        
        # If simple list of strings, convert
        if expectations and isinstance(expectations[0], str):
             expectations = [{"criterion": e, "importance": "Unknown", "met": "Unknown"} for e in expectations]
             
        df = pd.DataFrame(expectations)
        
        # Identify "Gap" (High importance + Not met)
        gaps = []
        if not df.empty and "met" in df.columns:
             # loose check for "False" or "No"
             gaps = df[df["met"].astype(str).str.lower().isin(["false", "no", "low"])]
        
        return {
            "expectations_table": df,
            "market_gaps": gaps if not isinstance(gaps, list) else pd.DataFrame()
        }

    # -------------------------------------------------------------------------
    # Block 5: Strategic Recommendation
    # -------------------------------------------------------------------------
    def recommend_positioning(self) -> Dict[str, str]:
        """
        Block 5: Actionable recommendation based on White Space (Gap).
        """
        # 1. Get Gaps
        demand_analysis = self.analyze_demand()
        gaps_df = demand_analysis["market_gaps"]
        
        # 2. Get Competitive Density (Clusters)
        diff_df = self.analyze_differentiation()
        clusters = diff_df["Positioning Cluster"].value_counts()
        
        # Logic
        # Recommendation = Target a Gap AND Avoid crowded clusters
        
        rec_title = "Positioning TBD"
        rec_desc = "No sufficient data to recommend."
        
        if not gaps_df.empty:
            top_gap = gaps_df.iloc[0]["criterion"]
            rec_title = f"Address Unmet Need: {top_gap}"
            rec_desc = f"The market signals a strong need for '{top_gap}' which is currently unsatisfied by major players."
        else:
            # Fallback algo: Look for least crowded cluster
            if not clusters.empty:
                least_common = clusters.idxmin()
                rec_title = f"Differentiate as {least_common}"
                rec_desc = f"The '{least_common}' space is less crowded compared to {clusters.idxmax()}. Opportunity to stand out."
        
        return {
            "strategy_title": rec_title,
            "rationale": rec_desc,
            "avoid": f"Direct confrontation in '{clusters.idxmax()}' segment" if not clusters.empty else "N/A"
        }

    # -------------------------------------------------------------------------
    # Helper: Sources Register
    # -------------------------------------------------------------------------
    def get_sources_dataframe(self) -> pd.DataFrame:
        """
        Retrieves all facts used in the analysis formatted for the Audit Table.
        Columns: ["Variable / Fact", "Valeur", "Source", "Type Source", "Méthode", "Confiance"]
        """
        # Fetch all facts related to competition
        # We can also fetch broad categories if we want to be exhaustive
        facts = self.mgr.get_facts(category="competition")
        
        data = []
        for f in facts:
            data.append({
                "Variable / Fact": f.get("key"),
                "Valeur": str(f.get("value")),
                "Source": f.get("source", "Unknown"),
                "Type Source": f.get("source_type", "N/A"),
                "Méthode": f.get("retrieval_method", "Direct"),
                "Confiance": f.get("confidence", "Medium")
            })
            
        if not data:
            return pd.DataFrame(columns=["Variable / Fact", "Valeur", "Source", "Type Source", "Méthode", "Confiance"])
            
        return pd.DataFrame(data)
