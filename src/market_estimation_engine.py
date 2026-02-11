from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Callable
import facts_manager
import pandas as pd
import re

import difflib

@dataclass
class EstimationStrategy:
    id: str
    name: str # e.g. "Bottom-up by User Base"
    formula_template: str # "{users} * {arpu}"
    required_inputs: Dict[str, str] # {"users": "total_active_users", "arpu": "avg_revenue_per_user"}
    description: str
    methodology_explanation: str = "" # NEW: Detailed explanation of "How we got here"
    market_reality_applied: bool = False # NEW: Track if reality factor was used
    # Future: add fallback_proxies logic

@dataclass
class EstimationResult:
    value: float
    formula_used: str
    calculation_details: str
    confidence: str
    missing_inputs: List[str]
    used_proxies: List[str]
    reality_factor: float = 1.0 # NEW
    market_friction_details: str = "" # NEW

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
    methodology_text: str = "" # NEW: Carries the explanation to UI
    strategic_narrative: str = "" # NEW: "So What?" analysis
    reality_score: str = "" # NEW: Displayable friction score

class MarketEstimationEngine:
    def __init__(self, facts_mgr):
        self.facts_mgr = facts_mgr
        # Fuzzy mapping dictionary (Canonical -> [Alias 1, Alias 2])
        self.fuzzy_mappings = {
            "total_potential_customers": ["target_audience", "total_users", "volume_clients", "potential_buyers", "target_volume"],
            "average_price": ["unit_price", "arpu", "selling_price", "license_cost", "subscription_fee"],
            "sam_percent": ["accessible_market_share", "sam_share", "serviceable_share"],
            "som_share": ["winnable_market_share", "som_percent", "market_penetration"],
            "production_volume": ["total_units", "active_install_base"],
            "tam_global_market": ["global_tam", "total_market_size"],
            "price_core": ["core_license_price", "base_price"],
            "price_modules": ["modules_revenue", "avg_module_price"],
            "price_services": ["service_fees", "implementation_cost"]
        }

    def _find_best_fuzzy_match(self, key: str) -> Optional[str]:
        """Attempts to find a key in facts_mgr that approximately matches the requested key."""
        all_keys = self.facts_mgr.get_all_keys()
        
        # 1. Check known aliases
        aliases = self.fuzzy_mappings.get(key, [])
        for alias in aliases:
            matches = difflib.get_close_matches(alias, all_keys, n=1, cutoff=0.8)
            if matches:
                return matches[0]
                
        # 2. General fuzzy match on the key itself
        matches = difflib.get_close_matches(key, all_keys, n=1, cutoff=0.7)
        if matches:
            return matches[0]
            
        return None

    def _get_fact(self, key: str) -> Optional[Dict]:
        """Helper to get full fact object with Fuzzy Logic fallback"""
        # 1. Exact Match
        facts = self.facts_mgr.get_facts(key=key)
        if facts: return facts[0]
        
        # 2. Fuzzy Match
        fuzzy_key = self._find_best_fuzzy_match(key)
        if fuzzy_key:
            # print(f"✨ Fuzzy Match: '{key}' -> '{fuzzy_key}'") # Debug log
            facts = self.facts_mgr.get_facts(key=fuzzy_key)
            if facts: return facts[0]
            
        return None

    def _get_fact_val_and_meta(self, key: str) -> (float, str, str):
        """Returns value, confidence, and source type for a key"""
        f = self._get_fact(key)
        if f and f.get("value") is not None:
            return f.get("value"), f.get("confidence", "low"), f.get("source_type", "Unknown")
        return None, "none", "missing"

    def _solve_strategy(self, strategy: EstimationStrategy, overrides: Dict[str, float] = None) -> EstimationResult:
        """
        Attempts to solve a specific strategy.
        Accepts overrides for Sensitivity Analysis.
        """
        inputs = {}
        missing = []
        proxies = []
        confidences = []
        details = []

        if overrides is None: overrides = {}

        # 1. Fetch Inputs
        for var_name, fact_key in strategy.required_inputs.items():
            # Check for override (Multiplier)
            # The override keys map to canonical fact keys (e.g., 'average_price')
            
            val, conf, src_type = self._get_fact_val_and_meta(fact_key)
            
            if val is None:
                missing.append(fact_key)
                inputs[var_name] = 0
            else:
                # Apply Override if exists
                # Logic: Override is a MULTIPLIER (e.g. 1.1 for +10%)
                # We need to map var_name (local) -> fact_key (global) -> match with overrides keys
                # Simplified: checks if 'fact_key' is in overrides
                multiplier = overrides.get(fact_key, 1.0)
                
                final_val = val * multiplier
                inputs[var_name] = final_val
                
                confidences.append(conf)
                
                src_label = src_type
                if multiplier != 1.0:
                    src_label += f" (Adj {int((multiplier-1)*100)}%)"
                    proxies.append(f"{var_name} Adjusted")
                
                if src_type in ["Proxy", "Estimation", "Interne"]:
                    proxies.append(f"{var_name} ({src_type})")
                
                # Format for display
                disp_val = final_val
                if isinstance(final_val, (int, float)) and final_val > 1000:
                    disp_val = f"{final_val:,.0f}"
                elif isinstance(final_val, float):
                    disp_val = f"{final_val:.2f}"
                    
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
        formula_filled = strategy.formula_template.format(**inputs)
        
        if not re.match(r'^[\d\.\s\+\-\*\/\(\)]+$', formula_filled):
             return EstimationResult(None, strategy.formula_template, "Formula Error", "low", [], [])
        
        try:
            value = eval(formula_filled)
        except Exception as e:
            return EstimationResult(None, strategy.formula_template, f"Calc Error: {e}", "low", [], [])

        # 3. Determine Confidence
        score = 0
        mapping = {"high": 3, "medium": 2, "low": 1, "none": 0}
        for c in confidences:
            score += mapping.get(c, 1)
        
        avg_score = score / len(confidences) if confidences else 0
        final_conf = "low"
        if avg_score >= 2.5: final_conf = "high"
        elif avg_score >= 1.5: final_conf = "medium"
        

        reality_factor = 1.0
        friction_details = ""
        
        if strategy.market_reality_applied:
            reality_factor, friction_details = self._calculate_market_reality_factor()
            value = value * reality_factor
            details.append(f"Reality Factor ({reality_factor:.0%})")
            
        return EstimationResult(
            value=value,
            formula_used=strategy.formula_template,
            calculation_details=f"{' x '.join(details)}",
            confidence=final_conf,
            missing_inputs=[],
            used_proxies=proxies,
            reality_factor=reality_factor,
            market_friction_details=friction_details
        )

    def _calculate_market_reality_factor(self) -> (float, str):
        """
        Calculates a 'Market Reality' friction coefficient (0 to 1).
        Based on: Sales Cycle, Tech Maturity, Competition.
        """
        # Default neutral values
        score = 1.0
        details = []
        
        # 1. Sales Cycle Friction (Longer = Lower Score)
        cycle, _, _ = self._get_fact_val_and_meta("sales_cycle_months")
        if cycle and cycle > 6:
            friction = 0.9 if cycle < 12 else 0.75
            score *= friction
            details.append(f"Sales Cycle Friction x{friction}")
            
        # 2. Tech Maturity (Low Maturity = Lower Score)
        # Assuming maturity is 1-10 or qualitative. Using dummy check for now or key existence.
        maturity, _, _ = self._get_fact_val_and_meta("market_maturity_score") # 0.0 to 1.0
        if maturity is not None:
             score *= (0.5 + (maturity * 0.5)) # Map 0->0.5, 1->1.0
             details.append(f"Maturity Adj x{(0.5 + (maturity * 0.5)):.2f}")
             
        # 3. Competition Intensity
        competitors, _, _ = self._get_fact_val_and_meta("competitor_count")
        
        comp_count = 0
        if isinstance(competitors, list):
            comp_count = len(competitors)
        elif isinstance(competitors, (int, float)):
             comp_count = competitors
             
        if comp_count > 50:
            score *= 0.9
            details.append("High Competition x0.9")
            
        return score, ", ".join(details) if details else "No friction applied"

    # -------------------------------------------------------------------------
    # Update all getter methods to pass overrides to run_component_solver
    # -------------------------------------------------------------------------

    def get_macro_estimation(self, overrides: Dict[str, float] = None) -> EstimationComponent:
        strategies = [
            EstimationStrategy(
                id="macro_tam_sam",
                name="Approche Standard (TAM Global x SAM%)",
                formula_template="{tam} * {sam_pct}",
                required_inputs={"tam": "tam_global_market", "sam_pct": "sam_percent"},
                description="Décomposition classique Top-Down.",
                methodology_explanation="On part de l'estimation du marché mondial total (TAM) issue de rapports sectoriels, puis on applique un filtre géographique et segmentaire (SAM %) pour isoler la part accessible."
            ),
             EstimationStrategy(
                id="macro_gdp",
                name="Approche Proxy PIB (PIB Secteur x Ratio)",
                formula_template="{gdp} * {ratio}",
                required_inputs={"gdp": "sector_gdp_proxy", "ratio": "sector_gdp_ratio"},
                description="Estimation basée sur le poids économique du secteur.",
                methodology_explanation="On utilise le Produit Intérieur Brut (PIB) du secteur cible comme proxy, auquel on applique un ratio historique de dépenses IT/Marketing pour estimer l'enveloppe budgétaire disponible."
            )
        ]
        return self._run_component_solver("comp_macro", "1. Estimation Macro (Top-down)", strategies, 
                                          "Fournir un ordre de grandeur global.", "#2196F3", overrides)

    def get_demand_estimation(self, overrides: Dict[str, float] = None) -> EstimationComponent:
        strategies = [
             EstimationStrategy(
                id="bu_segmented_pricing",
                name="Pricing Segmenté (Core + Services + Upsell)",
                formula_template="{vol} * ({p_core} + {p_mod} + {p_serv})",
                required_inputs={
                    "vol": "total_potential_customers", 
                    "p_core": "price_core", 
                    "p_mod": "price_modules", 
                    "p_serv": "price_services"
                },
                description="Haut niveau de précision grâce au mix-produit.",
                methodology_explanation="Au lieu d'un prix unique, on modélise l'ARPU réel en sommant la licence de base, les modules additionnels et les services (setup/formation). Cela reflète mieux la capture de valeur réelle (LTV).",
                market_reality_applied=True 
            ),
            EstimationStrategy(
                id="bu_volume_price",
                name="Volume x Prix (Acheteurs x Panier)",
                formula_template="{users} * {price}",
                required_inputs={"users": "total_potential_customers", "price": "average_price"},
                description="Approche canonique de la demande.",
                methodology_explanation="On multiplie le volume total de clients potentiels (Volume) par le panier moyen annuel (Prix/ARPU). C'est la méthode la plus robuste pour valider la réalité du terrain.",
                market_reality_applied=True 
            ),
             EstimationStrategy(
                id="bu_niche_penetration",
                name="Microniche (Pop. Cible x Pénétration x Prix)",
                formula_template="{pop} * {pen} * {price}",
                required_inputs={"pop": "target_segment_pop", "pen": "penetration_rate_proxy", "price": "average_price"},
                description="Approche pour segments sans base installée connue.",
                methodology_explanation="Pour les marchés émergents : on part de la population totale du segment, on estime un taux de pénétration réaliste à maturité, et on valorise par le prix unitaire.",
                market_reality_applied=True 
            )
        ]
        return self._run_component_solver("comp_demand", "2. Estimation par la Demande", strategies, 
                                          "Ancrer sur l'usage réel et la granularité client.", "#4CAF50", overrides)

    def get_supply_estimation(self, overrides: Dict[str, float] = None) -> EstimationComponent:
        strategies = [
            EstimationStrategy(
                id="sup_production",
                name="Production (Volume x Valeur Unitaire)",
                formula_template="{vol} * {uval}",
                required_inputs={"vol": "production_volume", "uval": "average_unit_market_value"},
                description="Approche industrielle / flux physiques.",
                methodology_explanation="Approche par les flux : on quantifie le volume total de biens/services produits ou vendus par l'ensemble des acteurs, multiplié par la valeur marchande unitaire."
            ),
             EstimationStrategy(
                id="sup_competitors",
                name="Somme des Revenus Concurrents (Part de Marché)",
                formula_template="{rev_sum} / {share_est}",
                required_inputs={"rev_sum": "competitors_revenue_sum", "share_est": "top_players_market_share"},
                description="Reconstitution via les parts de marché des leaders.",
                methodology_explanation="On somme les revenus connus des leaders du marché. Connaissant leur part de marché cumulée (ex: Top 3 = 60%), on fait une règle de trois pour retrouver la taille totale du marché."
            ),
            EstimationStrategy(
                id="sup_multiplier",
                name="Revenus Leaders x Multiplicateur Long Tail",
                formula_template="{rev_sum} * {mult}",
                required_inputs={"rev_sum": "top_players_cumulative_revenue", "mult": "market_multiplier_factor"},
                description="Extrapolation via la structure de marché (Règle de Pareto).",
                methodology_explanation="On utilise la 'Loi de puissance' (Long Tail). On prend les revenus cumulés du Top Players (ex: Pareto 80/20) et on applique un multiplicateur structurel pour inclure la multitude de petits acteurs."
            ),
            EstimationStrategy(
                id="sup_fragmentation_led",
                name="Multiplicateur Fragmentation",
                formula_template="{rev_sum} * (1 + {frag_idx})",
                required_inputs={"rev_sum": "top_players_cumulative_revenue", "frag_idx": "market_fragmentation_index"},
                description="Ajustement fin selon la concentration du marché.",
                methodology_explanation="Plus le marché est fragmenté (nombreux petits acteurs), plus le multiplicateur est élevé. Le 'Fragmentation Index' (0.1 à 3.0) approxime la part 'invisible' du marché."
            )
        ]
        return self._run_component_solver("comp_supply", "3. Estimation par l'Offre (Supply-Led)", strategies,
                                          "Reconstituer le marché par les flux de revenus.", "#FF9800", overrides)

    def _run_component_solver(self, id, name, strategies, role, color, overrides) -> EstimationComponent:
        best_res = None
        best_strat = None
        
        for strat in strategies:
            res = self._solve_strategy(strat, overrides)
            
            if res.value is not None:
                if best_res is None:
                    best_res = res
                    best_strat = strat
                else:
                    if res.confidence == "high" and best_res.confidence != "high":
                        best_res = res
                        best_strat = strat
        
        if best_res is None or best_res.value is None:
             default_strat = strategies[0]
             missing = []
             for k, v in default_strat.required_inputs.items():
                 if self._get_fact_val_and_meta(v)[0] is None:
                     missing.append(v)
             
             return EstimationComponent(
                id=id, name=name, role=role,
                method_description=f"Méthode proposée : {default_strat.name}",
                missing_data_strategy=f"Données manquantes : {', '.join(missing)}",
                estimated_value=None, status="empty", confidence="low", color=color,
                selected_strategy_name=default_strat.name,
                calculation_breakdown="Données insuffisantes"
            )

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
            calculation_breakdown=f"{best_res.calculation_details}",
            methodology_text=best_strat.methodology_explanation,
            reality_score=best_res.market_friction_details,
            strategic_narrative=self._generate_micro_narrative(best_strat, best_res)
        )

    def _generate_micro_narrative(self, strat: EstimationStrategy, res: EstimationResult) -> str:
        """Generates a short 'So What?' for the specific component."""
        msg = ""
        if res.reality_factor < 0.8:
            msg += "⚠ Marché théorique élevé mais friction d'adoption forte (Cycle/Maturité). "
        
        if "High Competition" in res.market_friction_details:
             msg += "Océan rouge : forte intensité concurrentielle détectée. "
             
        if strat.id == "bu_segmented_pricing":
            msg += "Le pricing composite révèle des poches de valeur via les services. "
            
        if not msg:
            msg = "Alignement sain entre hypothèses et volume."
            
        return msg

    def get_triangulated_estimation(self, comps: List[EstimationComponent]) -> EstimationComponent:
        """
        Calculates triangulation from explicitly passed components (which might have overrides).
        """
        valid = [c for c in comps if c.estimated_value is not None]
        
        if not valid:
            return EstimationComponent("comp_tria", "4. Triangulation", "Synthèse décisionnelle", "Moyenne des approches", [], "", None, "EUR", "low", "empty", "#9C27B0")
            
        vals = [c.estimated_value for c in valid]
        avg = sum(vals) / len(vals)
        
        details = " + ".join([f"{c.estimated_value:,.0f}" for c in valid])
        details = f"({details}) / {len(valid)}"
        
        return EstimationComponent(
            id="comp_tria",
            name="4. Triangulation & Décision",
            role="Synthèse robuste et arbitrage.",
            method_description=f"Moyenne pondérée de {len(valid)} méthodes.",
            data_used=[],
            estimated_value=avg,
            unit="EUR",
            confidence="medium" if len(valid) > 1 else "low",
            status="complete",
            color="#9C27B0",
            selected_strategy_name="Moyenne Arithmétique",
            calculation_breakdown=details,
            strategic_narrative="Consensus entre les méthodes. Réduit le risque d'erreur de modèle."
        )

    def get_all_estimations(self, overrides: Dict[str, float] = None) -> List[EstimationComponent]:
        c1 = self.get_macro_estimation(overrides)
        c2 = self.get_demand_estimation(overrides)
        c3 = self.get_supply_estimation(overrides)
        c4 = self.get_triangulated_estimation([c1, c2, c3])
        return [c1, c2, c3, c4]
        
    def determine_best_method(self, overrides: Dict[str, float] = None) -> EstimationComponent:
        all_comps = self.get_all_estimations(overrides)
        macro, demand, supply, triangulation = all_comps[0], all_comps[1], all_comps[2], all_comps[3]
        
        if triangulation.status == "complete" and triangulation.estimated_value is not None:
             match = re.search(r"\/ (\d+)", triangulation.method_description)
             if match and int(match.group(1)) >= 2:
                 return triangulation

        if demand.status == "complete": return demand
        if supply.status == "complete": return supply
        if macro.estimated_value is not None: return macro
            
        return macro

    def get_consolidated_facts_table(self) -> pd.DataFrame:
        # Same as before but updated logic
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
                "Type": f.get("source_type", "N/A"),
                "Confiance": f.get("confidence", "low").upper(),
                "Utilisé dans": used_in
            })
            
        if not data: return pd.DataFrame()
        return pd.DataFrame(data).sort_values(by="Utilisé dans", ascending=False)
        
    def get_waterfall_data(self, base_tam: float) -> pd.DataFrame:
        """
        Generates Waterfall Data (TAM -> SAM -> SOM).
        Uses facts if available, otherwise default ratios.
        """
        # 1. Get Ratios
        sam_pct, _, _ = self._get_fact_val_and_meta("sam_percent")
        som_share, _, _ = self._get_fact_val_and_meta("som_share")
        
        if sam_pct is None: sam_pct = 1.0 # Default to 100% if missing
        if som_share is None: som_share = 0.20 # Default to 20%
        
        sam_val = base_tam * sam_pct
        som_val = sam_val * som_share
        
        # Structure for Plotly Waterfall
        # Measure: "absolute", "relative", "relative", "total"
        # X: "TAM Global", "Segmentation", "Part de Marché", "SOM Estimé"
         
        return pd.DataFrame({
            "measure": ["absolute", "relative", "relative", "total"],
            "x": ["Total Addressable Market (TAM)", "Filtre Serviceable (SAM)", "Part Capturable (SOM)", "Revenus Potentiels"],
            "y": [base_tam, -(base_tam - sam_val), -(sam_val - som_val), som_val],
            "text": [f"{base_tam/1e6:.1f}M€", f"-{(1-sam_pct)*100:.0f}%", f"-{(1-som_share)*100:.0f}%", f"{som_val/1e6:.1f}M€"]
        })

    def generate_strategic_summary_text(self, tam: float, som: float) -> str:
        """Global Strategic Narrative"""
        ratio = som / tam if tam > 0 else 0
        
        if ratio < 0.05:
            return "Niche tactique : Le marché adressable est géant, mais votre cible actuelle est une fraction précise. Stratégie de 'Wedge' recommandée."
        elif ratio > 0.5:
             return "Dominance Play : Vous visez une part majeure du marché total. Attention à la réaction des incumbents."
        else:
             return "Marché équilibré : Ciblage cohérent avec le potentiel macro."

    def perform_sensitivity_analysis(
        self, 
        base_result: EstimationComponent,
        hypotheses: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Teste l'impact de variations ±20% sur chaque hypothèse/variable clé.
        
        Args:
            base_result: Composant d'estimation de référence
            hypotheses: Liste des hypothèses à tester (si fournie par LLM)
            
        Returns:
            {
                "base_value": float,
                "tests": List[Dict],
                "most_sensitive_variables": List[str],
                "confidence_adjusted": str
            }
        """
        if base_result.estimated_value is None:
            return {
                "base_value": None,
                "tests": [],
                "most_sensitive_variables": [],
                "confidence_adjusted": "LOW",
                "error": "No base value to test"
            }
        
        base_value = base_result.estimated_value
        
        # Identifier les variables clés à tester
        test_variables = []
        
        # 1. Depuis les hypothèses LLM si disponibles
        if hypotheses:
            for hyp in hypotheses:
                fact_key = hyp.get("variable") or hyp.get("key")
                if fact_key:
                    test_variables.append({
                        "key": fact_key,
                        "name": hyp.get("name", fact_key),
                        "base_value": hyp.get("central_value") or hyp.get("value"),
                        "unit": hyp.get("unit", "")
                    })
        
        # 2. Sinon, depuis data_used du composant
        if not test_variables and base_result.data_used:
            for fact in base_result.data_used:
                test_variables.append({
                    "key": fact.get("key"),
                    "name": fact.get("key", "").replace("_", " ").title(),
                    "base_value": fact.get("value"),
                    "unit": fact.get("unit", "")
                })
        
        tests_results = []
        sensitivity_scores = {}
        
        for var in test_variables:
            if not var["base_value"]:
                continue
            
            # Test -20%
            override_low = {var["key"]: 0.8}  # Multiplier 0.8
            comps_low = self.get_all_estimations(overrides=override_low)
            
            # Re-identifier le composant équivalent à base_result
            comp_low = next((c for c in comps_low if c.id == base_result.id), None)
            value_low = comp_low.estimated_value if comp_low else None
            
            # Test +20%
            override_high = {var["key"]: 1.2}  # Multiplier 1.2
            comps_high = self.get_all_estimations(overrides=override_high)
            comp_high = next((c for c in comps_high if c.id == base_result.id), None)
            value_high = comp_high.estimated_value if comp_high else None
            
            if value_low and value_high:
                delta_low_pct = ((value_low - base_value) / base_value) * 100
                delta_high_pct = ((value_high - base_value) / base_value) * 100
                
                # Score de sensibilité = amplitude de variation moyenne
                sensitivity_score = (abs(delta_low_pct) + abs(delta_high_pct)) / 2
                sensitivity_scores[var["name"]] = sensitivity_score
                
                # Classification
                if sensitivity_score > 30:
                    sensitivity_class = "CRITICAL"
                elif sensitivity_score > 15:
                    sensitivity_class = "HIGH"
                elif sensitivity_score > 5:
                    sensitivity_class = "MEDIUM"
                else:
                    sensitivity_class = "LOW"
                
                tests_results.append({
                    "hypothesis": var["name"],
                    "base": var["base_value"],
                    "unit": var["unit"],
                    "low_scenario": {
                        "value": var["base_value"] * 0.8,
                        "result": value_low,
                        "delta_pct": round(delta_low_pct, 1)
                    },
                    "high_scenario": {
                        "value": var["base_value"] * 1.2,
                        "result": value_high,
                        "delta_pct": round(delta_high_pct, 1)
                    },
                    "sensitivity_score": sensitivity_class
                })
        
        # Identifier les variables les plus sensibles
        most_sensitive = sorted(
            sensitivity_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        most_sensitive_names = [name for name, _ in most_sensitive]
        
        # Ajuster confiance si haute sensibilité
        max_sensitivity = most_sensitive[0][1] if most_sensitive else 0
        
        if max_sensitivity > 30:
            confidence_adjusted = "LOW"
        elif max_sensitivity > 15:
            confidence_adjusted = "MEDIUM"
        else:
            confidence_adjusted = base_result.confidence.upper()
        
        return {
            "base_value": base_value,
            "tests": tests_results,
            "most_sensitive_variables": most_sensitive_names,
            "confidence_adjusted": confidence_adjusted,
            "max_sensitivity_score": round(max_sensitivity, 1) if most_sensitive else 0
        }

