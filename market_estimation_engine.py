from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Callable
import facts_manager
import pandas as pd
import re

@dataclass
class EstimationStrategy:
    id: str
    name: str # e.g. "Bottom-up by User Base"
    formula_template: str # "{users} * {arpu}"
    required_inputs: Dict[str, str] # {"users": "total_active_users", "arpu": "avg_revenue_per_user"}
    description: str
    # Future: add fallback_proxies logic

@dataclass
class EstimationResult:
    value: float
    formula_used: str
    calculation_details: str
    confidence: str
    missing_inputs: List[str]
    used_proxies: List[str]

@dataclass
class EstimationComponent:
    id: str
    name: str
    role: str
    method_description: str
    data_used: List[Dict[str, Any]] = field(default_factory=list)
    missing_data_strategy: str = ""
    estimated_value: Optional[float] = None
    unit: str = "EUR"
    confidence: str = "low"
    status: str = "empty"
    color: str = "#9e9e9e"
    
    # New Granular Fields
    selected_strategy_name: str = ""
    calculation_breakdown: str = ""

class MarketEstimationEngine:
    def __init__(self, facts_mgr):
        self.facts_mgr = facts_mgr

    def _get_fact(self, key: str) -> Optional[Dict]:
        """Helper to get full fact object"""
        facts = self.facts_mgr.get_facts(key=key)
        # Prioritize "override" or most recent? For now take first.
        return facts[0] if facts else None

    def _get_fact_val_and_meta(self, key: str) -> (float, str, str):
        """Returns value, confidence, and source type for a key"""
        f = self._get_fact(key)
        if f and f.get("value") is not None:
            # Handle percentage values stored as whole numbers or floats?
            # Standardize: stored as is. Formula handles conversion if needed.
            return f.get("value"), f.get("confidence", "low"), f.get("source_type", "Unknown")
        return None, "none", "missing"

    def _solve_strategy(self, strategy: EstimationStrategy) -> EstimationResult:
        """
        Attempts to solve a specific strategy.
        Returns the result and metadata.
        """
        inputs = {}
        missing = []
        proxies = []
        confidences = []
        
        details = []

        # 1. Fetch Inputs
        for var_name, fact_key in strategy.required_inputs.items():
            val, conf, src_type = self._get_fact_val_and_meta(fact_key)
            
            if val is None:
                missing.append(fact_key)
                inputs[var_name] = 0 # Placeholder to prevent eval crash, but will fail check
            else:
                inputs[var_name] = val
                confidences.append(conf)
                if src_type in ["Proxy", "Estimation", "Interne"]:
                    proxies.append(f"{var_name} ({src_type})")
                
                # Format for display
                disp_val = val
                if isinstance(val, (int, float)) and val > 1000:
                    disp_val = f"{val:,.0f}"
                details.append(f"{var_name}=[{disp_val}]")

        if missing:
            return EstimationResult(
                value=None,
                formula_used=strategy.formula_template,
                calculation_details="Missing: " + ", ".join(missing),
                confidence="low",
                missing_inputs=missing,
                used_proxies=proxies
            )

        # 2. Evaluate Formula
        # Safe evaluation of math expression
        formula_filled = strategy.formula_template.format(**inputs)
        
        # Security check: only allow simple math
        if not re.match(r'^[\d\.\s\+\-\*\/\(\)]+$', formula_filled):
             return EstimationResult(None, strategy.formula_template, "Formula Error", "low", [], [])
        
        try:
            value = eval(formula_filled)
        except Exception as e:
            return EstimationResult(None, strategy.formula_template, f"Calc Error: {e}", "low", [], [])

        # 3. Determine Confidence
        # Logic: Average of inputs. If any proxy, lower confidence.
        score = 0
        mapping = {"high": 3, "medium": 2, "low": 1, "none": 0}
        for c in confidences:
            score += mapping.get(c, 1)
        
        avg_score = score / len(confidences) if confidences else 0
        final_conf = "low"
        if avg_score >= 2.5: final_conf = "high"
        elif avg_score >= 1.5: final_conf = "medium"
        
        return EstimationResult(
            value=value,
            formula_used=strategy.formula_template,
            calculation_details=f"{' x '.join(details)}",
            confidence=final_conf,
            missing_inputs=[],
            used_proxies=proxies
        )

    def get_macro_estimation(self) -> EstimationComponent:
        strategies = [
            EstimationStrategy(
                id="macro_tam_sam",
                name="Approche Standard (TAM Global x SAM%)",
                formula_template="{tam} * {sam_pct}",
                required_inputs={"tam": "tam_global_market", "sam_pct": "sam_percent"},
                description="Décomposition classique Top-Down."
            ),
             EstimationStrategy(
                id="macro_gdp",
                name="Approche Proxy PIB (PIB Secteur x Ratio)",
                formula_template="{gdp} * {ratio}",
                required_inputs={"gdp": "sector_gdp_proxy", "ratio": "sector_gdp_ratio"},
                description="Estimation basée sur le poids économique du secteur."
            )
        ]
        
        return self._run_component_solver("comp_macro", "1. Estimation Macro (Top-down)", strategies, 
                                          "Fournir un ordre de grandeur global.", "#2196F3")

    def get_demand_estimation(self) -> EstimationComponent:
        strategies = [
            EstimationStrategy(
                id="bu_volume_price",
                name="Volume x Prix (Acheteurs x Panier)",
                formula_template="{users} * {price}",
                required_inputs={"users": "total_potential_customers", "price": "average_price"},
                description="Approche canonique de la demande."
            ),
             EstimationStrategy(
                id="bu_niche_penetration",
                name="Microniche (Pop. Cible x Pénétration x Prix)",
                formula_template="{pop} * {pen} * {price}",
                required_inputs={"pop": "target_segment_pop", "pen": "penetration_rate_proxy", "price": "average_price"},
                description="Approche pour segments sans base installée connue."
            )
        ]
        return self._run_component_solver("comp_demand", "2. Estimation par la Demande", strategies, 
                                          "Ancrer sur l'usage réel et la granularité client.", "#4CAF50")

    def get_supply_estimation(self) -> EstimationComponent:
        strategies = [
            EstimationStrategy(
                id="sup_production",
                name="Production (Volume x Valeur Unitaire)",
                formula_template="{vol} * {uval}",
                required_inputs={"vol": "production_volume", "uval": "average_unit_market_value"},
                description="Approche industrielle / flux physiques."
            ),
             EstimationStrategy(
                id="sup_competitors",
                name="Somme des Revenus Concurrents (Part de Marché)",
                formula_template="{rev_sum} / {share_est}",
                required_inputs={"rev_sum": "competitors_revenue_sum", "share_est": "top_players_market_share"},
                description="Reconstitution via les parts de marché des leaders."
            ),
            EstimationStrategy(
                id="sup_multiplier",
                name="Revenus Leaders x Multiplicateur Long Tail",
                formula_template="{rev_sum} * {mult}",
                required_inputs={"rev_sum": "top_players_cumulative_revenue", "mult": "market_multiplier_factor"},
                description="Extrapolation via la structure de marché (Règle de Pareto)."
            )
        ]
        return self._run_component_solver("comp_supply", "3. Estimation par l'Offre (Supply-Led)", strategies,
                                          "Reconstituer le marché par les flux de revenus.", "#FF9800")

    def _run_component_solver(self, id, name, strategies, role, color) -> EstimationComponent:
        best_res = None
        best_strat = None
        
        # Find best valid strategy
        # Priority: Completed > High Confidence > Medium Confidence
        
        for strat in strategies:
            res = self._solve_strategy(strat)
            
            if res.value is not None:
                # If we don't have a result yet, take this one
                if best_res is None:
                    best_res = res
                    best_strat = strat
                else:
                    # Generic comparison: Prefer High Confidence
                    if res.confidence == "high" and best_res.confidence != "high":
                        best_res = res
                        best_strat = strat
        
        # If no result found, use the first strategy as formatting template (with empty values)
        if best_res is None or best_res.value is None:
             default_strat = strategies[0]
             # Check what inputs are missing for the default strategy
             missing = []
             for k, v in default_strat.required_inputs.items():
                 if self._get_fact(v) is None or self._get_fact(v).get("value") is None:
                     missing.append(v)
             
             return EstimationComponent(
                id=id, name=name, role=role,
                method_description=f"Méthode proposée : {default_strat.name}",
                missing_data_strategy=f"Données manquantes : {', '.join(missing)}",
                estimated_value=None, status="empty", confidence="low", color=color,
                selected_strategy_name=default_strat.name,
                calculation_breakdown="Données insuffisantes"
            )

        # Collect data used for UI
        used_facts = []
        for v in best_strat.required_inputs.values():
            f = self._get_fact(v)
            if f: used_facts.append(f)

        return EstimationComponent(
            id=id, name=name, role=role,
            method_description=best_strat.description,
            data_used=used_facts,
            missing_data_strategy="Données complètes (ou proxies utilisés).",
            estimated_value=best_res.value,
            unit="EUR",
            confidence=best_res.confidence,
            status="complete",
            color=color,
            selected_strategy_name=best_strat.name,
            calculation_breakdown=f"{best_res.calculation_details}"
        )

    def get_triangulated_estimation(self) -> EstimationComponent:
        # Aggregate results from other components
        comps = [
            self.get_macro_estimation(),
            self.get_demand_estimation(),
            self.get_supply_estimation()
        ]
        
        valid = [c for c in comps if c.estimated_value is not None]
        
        if not valid:
            return EstimationComponent("comp_tria", "4. Triangulation", "Synthèse décisionnelle", "Moyenne des approches", [], "", None, "EUR", "low", "empty", "#9C27B0")
            
        vals = [c.estimated_value for c in valid]
        avg = sum(vals) / len(vals)
        
        # Identification of divergence
        details = " + ".join([f"{c.estimated_value:,.0f}" for c in valid])
        details = f"({details}) / {len(valid)}"
        
        return EstimationComponent(
            id="comp_tria",
            name="4. Triangulation & Décision",
            role="Synthèse robuste et arbitrage.",
            method_description=f"Moyenne pondérée de {len(valid)} méthodes.",
            data_used=[], # Derived
            estimated_value=avg,
            unit="EUR",
            confidence="medium" if len(valid) > 1 else "low",
            status="complete",
            color="#9C27B0",
            selected_strategy_name="Moyenne Arithmétique",
            calculation_breakdown=details
        )

    def get_all_estimations(self) -> List[EstimationComponent]:
        return [
            self.get_macro_estimation(),
            self.get_demand_estimation(),
            self.get_supply_estimation(),
            self.get_triangulated_estimation()
        ]

    def get_consolidated_facts_table(self) -> pd.DataFrame:
        # Same as before but updated logic
         # 1. Get Usage Map (to tag used facts)
        comps = self.get_all_estimations()
        usage_map = {}
        for comp in comps:
             for fact in comp.data_used:
                 f_key = fact.get("key")
                 if f_key not in usage_map: usage_map[f_key] = []
                 usage_map[f_key].append(comp.name.split(".")[0])
        
        all_facts = self.facts_mgr.facts
        data = []
        for f in all_facts:
            key = f.get("key")
            val_display = f['value']
            if isinstance(val_display, (int, float)) and val_display > 1000:
                val_display = f"{val_display:,.0f}"
            
            used_in = ", ".join(usage_map.get(key, []))
            if not used_in: used_in = "-"
            
            data.append({
                "Variable / Fact": key.replace("_", " ").title(),
                "Valeur": f"{val_display} {f.get('unit','')}",
                "Source": f.get("source", "N/A"),
                "Type": f.get("source_type", "N/A"), # New Col
                "Confiance": f.get("confidence", "low").upper(),
                "Utilisé dans": used_in
            })
            
        if not data: return pd.DataFrame()
        return pd.DataFrame(data).sort_values(by="Utilisé dans", ascending=False)

    def determine_best_method(self) -> EstimationComponent:
        """
        Adaptively selects the best available estimation method.
        Priority:
        1. Triangulation (if valid and based on >1 method)
        2. Demand (Bottom-Up) (if complete)
        3. Supply (if complete)
        4. Macro (Top-Down) (fallback)
        """
        all_comps = self.get_all_estimations()
        macro, demand, supply, triangulation = all_comps[0], all_comps[1], all_comps[2], all_comps[3]
        
        # 1. Triangulation - If based on multiple methods
        if triangulation.status == "complete" and triangulation.estimated_value is not None:
             match = re.search(r"\/ (\d+)", triangulation.method_description)
             if match:
                 count = int(match.group(1))
                 if count >= 2:
                     return triangulation

        # 2. Demand - Bottom Up is preferred for granularity
        if demand.status == "complete":
            return demand
            
        # 3. Supply
        if supply.status == "complete":
            return supply
            
        # 4. Fallback to Macro (or whatever has value)
        if macro.estimated_value is not None:
            return macro
            
        return macro # Even if empty, return first component structure
