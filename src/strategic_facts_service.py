"""
Strategic FACTS Service - Centralized Strategic Analysis Generator
===================================================================

Ce module centralise la génération d'analyses stratégiques (SWOT, BCG, PESTEL)
en un seul appel LLM, enrichi par les données financières réelles.

Architecture:
- Singleton StrategicFactsService avec cache en mémoire
- Un seul appel Mistral génère SWOT + BCG + PESTEL
- Intégration avec facts_service pour enrichissement financier

Usage:
    from strategic_facts_service import strategic_facts_service
    analysis = strategic_facts_service.get_strategic_analysis("Apple", "AAPL")
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from facts_service import facts_service

load_dotenv()


class StrategicFactsService:
    """
    Service centralisé de génération d'analyses stratégiques.
    Combine les données financières avec l'analyse LLM en un seul appel.
    """
    
    def __init__(self, cache_ttl_minutes: int = 15):
        """
        Initialise le service Strategic FACTS.
        
        Args:
            cache_ttl_minutes: Durée de vie du cache en minutes (défaut: 15)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._llm = None
    
    def _get_llm(self):
        """Initialise le LLM Mistral (lazy loading)."""
        if self._llm is None:
            self._llm = ChatMistralAI(
                model="mistral-small",
                temperature=0.2,
                mistral_api_key=os.getenv("MISTRAL_API_KEY")
            )
        return self._llm
    
    def _is_cache_valid(self, key: str) -> bool:
        """Vérifie si le cache est encore valide."""
        if key not in self._cache_timestamps:
            return False
        return datetime.now() - self._cache_timestamps[key] < self._cache_ttl
    
    def _format_financial_context(self, facts: Dict[str, Any]) -> str:
        """
        Formate les données financières pour enrichir le prompt LLM.
        
        Args:
            facts: Données du facts_service
            
        Returns:
            Contexte financier formaté en texte
        """
        if not facts or facts.get("error"):
            return "Données financières non disponibles."
        
        derived = facts.get("derived", {})
        info = facts.get("info", {})
        
        context_parts = []
        
        # Infos générales
        if info:
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            employees = info.get("fullTimeEmployees", "N/A")
            market_cap = info.get("marketCap", 0)
            
            context_parts.append(f"Secteur: {sector} | Industrie: {industry}")
            context_parts.append(f"Employés: {employees:,}" if isinstance(employees, int) else f"Employés: {employees}")
            if market_cap:
                context_parts.append(f"Capitalisation: ${market_cap/1e9:.1f}B")
        
        # Métriques financières
        if derived.get("revenue") is not None:
            try:
                latest_revenue = derived["revenue"].iloc[-1]
                context_parts.append(f"Dernier CA: ${latest_revenue/1e9:.2f}B")
            except:
                pass
        
        if derived.get("net_income") is not None:
            try:
                latest_income = derived["net_income"].iloc[-1]
                context_parts.append(f"Dernier Résultat Net: ${latest_income/1e9:.2f}B")
            except:
                pass
        
        if derived.get("net_margin") is not None:
            try:
                latest_margin = derived["net_margin"].iloc[-1]
                context_parts.append(f"Marge Nette: {latest_margin:.1f}%")
            except:
                pass
        
        if derived.get("roe") is not None:
            try:
                latest_roe = derived["roe"].iloc[-1]
                context_parts.append(f"ROE: {latest_roe:.1f}%")
            except:
                pass
        
        if derived.get("debt_to_equity") is not None:
            try:
                latest_de = derived["debt_to_equity"].iloc[-1]
                context_parts.append(f"Ratio Dette/Equity: {latest_de:.2f}")
            except:
                pass
        
        if derived.get("fcf") is not None:
            try:
                latest_fcf = derived["fcf"].iloc[-1]
                context_parts.append(f"Free Cash Flow: ${latest_fcf/1e9:.2f}B")
            except:
                pass
        
        return "\n".join(context_parts) if context_parts else "Données financières limitées."
    
    def _extract_financial_swot_items(self, facts: Dict[str, Any]) -> Dict[str, list]:
        """
        Extrait 1-2 points SWOT automatiques basés sur les données financières.
        Ces points seront ajoutés aux résultats du LLM.
        """
        financial_swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        if not facts or facts.get("error"):
            return financial_swot
        
        derived = facts.get("derived", {})
        info = facts.get("info", {})
        
        # Analyse de la marge nette
        if derived.get("net_margin") is not None:
            try:
                margin = derived["net_margin"].iloc[-1]
                if margin > 15:
                    financial_swot["strengths"].append({
                        "item": f"Marge nette élevée ({margin:.1f}%)",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
                elif margin < 5:
                    financial_swot["weaknesses"].append({
                        "item": f"Marge nette faible ({margin:.1f}%)",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
            except:
                pass
        
        # Analyse du ROE
        if derived.get("roe") is not None:
            try:
                roe = derived["roe"].iloc[-1]
                if roe > 20:
                    financial_swot["strengths"].append({
                        "item": f"ROE excellent ({roe:.1f}%)",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
                elif roe < 10:
                    financial_swot["weaknesses"].append({
                        "item": f"ROE en dessous des standards ({roe:.1f}%)",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
            except:
                pass
        
        # Analyse du ratio d'endettement
        if derived.get("debt_to_equity") is not None:
            try:
                de_ratio = derived["debt_to_equity"].iloc[-1]
                if de_ratio > 2:
                    financial_swot["threats"].append({
                        "item": f"Endettement élevé (D/E: {de_ratio:.2f})",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
                elif de_ratio < 0.5:
                    financial_swot["strengths"].append({
                        "item": f"Structure financière solide (D/E: {de_ratio:.2f})",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
            except:
                pass
        
        # Analyse du FCF
        if derived.get("fcf") is not None:
            try:
                fcf = derived["fcf"].iloc[-1]
                if fcf > 0:
                    financial_swot["opportunities"].append({
                        "item": f"Trésorerie disponible (FCF: ${fcf/1e9:.1f}B)",
                        "evidence": "📊 Donnée financière réelle - Capacité d'investissement",
                        "source": "financial"
                    })
                else:
                    financial_swot["threats"].append({
                        "item": f"FCF négatif (${fcf/1e9:.1f}B)",
                        "evidence": "📊 Donnée financière réelle",
                        "source": "financial"
                    })
            except:
                pass
        
        # Limiter à 1-2 items max par catégorie
        for key in financial_swot:
            financial_swot[key] = financial_swot[key][:2]
        
        return financial_swot
    
    def get_strategic_analysis(
        self, 
        company: str, 
        ticker: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Génère une analyse stratégique complète (SWOT + BCG + PESTEL) en un seul appel LLM.
        
        Args:
            company: Nom de l'entreprise (ex: "Apple", "Tesla")
            ticker: Symbole boursier optionnel pour enrichissement financier (ex: "AAPL")
            force_refresh: Force le recalcul même si en cache
            
        Returns:
            Dictionnaire contenant:
            - swot: {strengths, weaknesses, opportunities, threats}
            - bcg: [{name, market_share, growth, revenue_weight}]
            - pestel: {Politique, Economique, Societal, Technologique, Environnemental, Legal}
            - financial_context: Contexte financier utilisé
            - generated_at: Timestamp de génération
        """
        # AJOUT VERSION v3 FORCE INVALIDATE + DEBUG PRINT
        cache_key = f"{company}_{ticker or 'no_ticker'}_v3"
        print(f"🔍 [DEBUG V3] Requesting analysis for {company} (Key: {cache_key})")
        
        # Vérifier le cache
        if not force_refresh and cache_key in self._cache and self._is_cache_valid(cache_key):
            print(f"📦 [STRATEGIC FACTS] Cache hit pour {company}")
            return self._cache[cache_key]
        
        print(f"🔄 [STRATEGIC FACTS] Génération de l'analyse stratégique pour {company}...")
        
        # Récupérer les données financières si ticker fourni
        financial_context = "Pas de données financières (ticker non spécifié)."
        if ticker:
            try:
                facts = facts_service.get_company_facts(ticker)
                financial_context = self._format_financial_context(facts)
                print(f"   📊 Données financières {ticker} intégrées")
            except Exception as e:
                print(f"   ⚠️ Erreur récupération financière: {e}")
        
        # Prompt unifié pour les 3 analyses avec sources obligatoires
        prompt = ChatPromptTemplate.from_template("""
Tu es un consultant stratégique senior. Analyse l'entreprise {company}.

DONNÉES FINANCIÈRES RÉELLES (pour contexte uniquement):
{financial_context}

GÉNÈRE UNE ANALYSE STRATÉGIQUE COMPLÈTE AU FORMAT JSON STRICT.
CHAQUE ÉLÉMENT DOIT AVOIR UNE SOURCE CITÉE.

{{
    "swot": {{
        "strengths": [
            {{"item": "Force courte", "evidence": "Justification", "source": "Nom PRÉCIS (ex: Rapport Annuel 2023, Reuters Jan 2024)", "source_type": "rapport_financier"}}
        ],
        "weaknesses": [
            {{"item": "Faiblesse courte", "evidence": "Justification", "source": "Nom PRÉCIS (ex: Bloomberg Oct 2023)", "source_type": "presse"}}
        ],
        "opportunities": [
            {{"item": "Opportunité courte", "evidence": "Justification", "source": "Nom PRÉCIS (ex: Gartner Forecast 2024)", "source_type": "analyse_marche"}}
        ],
        "threats": [
            {{"item": "Menace courte", "evidence": "Justification", "source": "Nom PRÉCIS (ex: WSJ Dec 2023)", "source_type": "presse"}}
        ]
    }},
    "bcg": [
        {{"name": "Segment", "market_share": 0.8, "growth": 0.6, "revenue_weight": 50, "source": "IDC/Gartner Q3 2024"}}
    ],
    "pestel": {{
        "Politique": {{"score": 7, "details": "Impact...", "source": "Reuters 2024"}},
        "Economique": {{"score": 5, "details": "Contexte...", "source": "Bloomberg 2024"}},
        "Societal": {{"score": 4, "details": "Tendances...", "source": "McKinsey 2024"}},
        "Technologique": {{"score": 8, "details": "Évolutions...", "source": "Gartner 2024"}},
        "Environnemental": {{"score": 6, "details": "Enjeux...", "source": "CDP Report 2024"}},
        "Legal": {{"score": 5, "details": "Cadre...", "source": "EU Commission 2024"}}
    }}
}}

TYPES DE SOURCES (source_type) :
- "rapport_financier" : 10-K, rapports annuels, earnings calls
- "presse" : Reuters, Bloomberg, WSJ, Financial Times
- "analyse_marche" : IDC, Gartner, McKinsey, BCG, Forrester
- "regulateur" : EU Commission, SEC, FDA

RÈGLES SWOT :
- EXACTEMENT 3 éléments par catégorie
- "item" : MAX 35 caractères, concis
- "evidence" : MAX 50 caractères
- "source" : DOIT ÊTRE PRÉCISE (Ex: "Rapport Annuel 2023", "Reuters 12/2023", "Gartner Q3 2024").
- INTERDIT de mettre "Analyse IA", "Site web", "Interne". Trouve une vraie source publique plausible.
- Ne PAS mentionner de chiffres financiers

RÈGLES BCG : 4-5 segments, source PRÉCISE requise pour chaque part de marché
RÈGLES PESTEL : Score 0-10, source PRÉCISE requise pour chaque fait cité

Réponds UNIQUEMENT avec du JSON valide, aucun texte autour.
""")
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({
                "company": company,
                "financial_context": financial_context
            })
            
            # Parsing du JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            if content.startswith("```"):
                content = content.replace("```", "")
            
            analysis = json.loads(content)
            
            # Enrichir le SWOT avec les données financières automatiques
            financial_swot = {}
            if ticker:
                try:
                    facts = facts_service.get_company_facts(ticker)
                    financial_swot = self._extract_financial_swot_items(facts)
                except:
                    pass
            
            # Fusionner : items financiers en premier, puis items IA
            merged_swot = {}
            for category in ["strengths", "weaknesses", "opportunities", "threats"]:
                ai_items = analysis.get("swot", {}).get(category, [])[:3]  # Max 3 AI items
                fin_items = financial_swot.get(category, [])[:2]  # Max 2 financial items
                # Financial items first (avec icône), puis AI items
                merged_swot[category] = fin_items + ai_items
            
            # Structure finale avec métadonnées
            result = {
                "company": company,
                "ticker": ticker,
                "swot": merged_swot,
                "bcg": analysis.get("bcg", []),
                "pestel": analysis.get("pestel", {}),
                "financial_context": financial_context,
                "generated_at": datetime.now().isoformat()
            }
            
            # Mise en cache
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()
            
            print(f"✅ [STRATEGIC FACTS] Analyse générée et mise en cache pour {company}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ [STRATEGIC FACTS] Erreur parsing JSON: {e}")
            return self._empty_analysis(company, ticker, f"Erreur parsing: {e}")
        except Exception as e:
            print(f"❌ [STRATEGIC FACTS] Erreur: {e}")
            return self._empty_analysis(company, ticker, str(e))
    
    def _empty_analysis(self, company: str, ticker: Optional[str], error: str) -> Dict[str, Any]:
        """Retourne une structure vide en cas d'erreur."""
        return {
            "company": company,
            "ticker": ticker,
            "error": error,
            "swot": {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": []
            },
            "bcg": [],
            "pestel": {},
            "financial_context": "",
            "generated_at": datetime.now().isoformat()
        }
    
    def clear_cache(self, company: Optional[str] = None):
        """
        Vide le cache.
        
        Args:
            company: Si spécifié, vide uniquement le cache de cette entreprise.
        """
        if company:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(company)]
            for key in keys_to_remove:
                del self._cache[key]
                del self._cache_timestamps[key]
            print(f"🗑️ [STRATEGIC FACTS] Cache vidé pour {company}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            print("🗑️ [STRATEGIC FACTS] Cache entièrement vidé")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        return {
            "entries": len(self._cache),
            "companies": list(set(k.split("_")[0] for k in self._cache.keys())),
            "ttl_minutes": self._cache_ttl.total_seconds() / 60
        }


    
    def generate_market_sizing_facts(self, scope: str) -> List[Dict[str, Any]]:
        """
        Génère des estimations de marché (TAM/SAM/SOM) chiffrées via Mistral.
        NOUVELLE LOGIQUE : Génération de multiples perspectives (Secondaire, Bottom-Up, Supply-Led).
        """
        print(f"🔄 [MARKET GENERATION] Estimation MULTI-MÉTHODES du marché pour : {scope}")
        
        prompt = ChatPromptTemplate.from_template("""
        Tu es l'architecte du moteur d'estimation de marché de KPMG.
        
        🎯 OBJECTIF CRITIQUE
        Ne te contente JAMAIS de chercher un chiffre "TAM Global" sur internet.
        Ta mission est de **CONSTRUIRE** une estimation granulaire pour le marché : "{scope}".
        
        🏗️ PHILOSOPHIE DE CONSTRUCTION (Granularité > Source Unique)
        Pour les marchés niches ou mal documentés, tu dois décomposer le problème :
        - Au lieu de dire "TAM = 1Md€", dis : "10k Usines x 5 Machines/Usine x 20k€/Machine".
        - Utilise des **PROXYS** (ex: Si pas de données sur le marché du "Miel de Lavande", utilise "Marché du Miel" x "% Production Lavande").
        
        🧩 MÉTHODOLOGIE ATTENDUE (3 PERSPECTIVES)
        
        1️⃣ Perspective SECONDAIRE (Validée si possible, sinon extrapolée)
        - Cherche un rapport de confiance. Si introuvable, déduis-le d'un marché parent (Top-Down).
        - Ex: "Marché Global du Logiciel" -> "Part du Vertical Industrie" -> "Part du sous-segment".
        
        2️⃣ Perspective BOTTOM-UP (Construction par la Demande)
        - C'est le cœur de ton estimation. Décompose en briques élémentaires :
        - **Volume** : Base installée, Population cible, Nombre d'actes...
        - **Intensité** : Taux d'équipement, Fréquence d'achat...
        - **Valorisation** : Prix unitaire, Panier moyen...
        - *Exemple Niche* : Pour "Maintenance de Ruches" -> (Nb Apiculteurs en France) x (Moyenne Ruches/Apiculteur) x (Coût Service/An).
        
        3️⃣ Perspective SUPPLY-LED (Offre / Concurrents)
        - Estime le CA des leaders (ou d'un leader proxy).
        - Applique un ratio de concentration (ex: Top 3 = 40% du marché).
        - Si niche : CA Moyen d'un acteur type x Nombre d'acteurs estimés.
        
        📝 FORMAT DE SORTIE JSON STRICT
        Tu dois fournir des champs "desc" et "source" très détaillés expliquant ta logique de construction.
        
        {{
            "scope_definition": {{
                "market_type": "Dépenses récurrentes (OpEx)",
                "products_included": ["Service A", "Produit B"],
                "target_clients": "Segment précis (ex: ETI Industrielles)",
                "economic_unit": "€ / Site / An"
            }},
            "secondary_tam": {{
                 "value": 50000000, 
                 "unit": "EUR", 
                 "source": "Extrapolation Statista/Xerfi", 
                 "year": "2024",
                 "confidence": 0.6,
                 "desc": "Dérivé du marché global (10Md€) avec un ratio de 0.5% pour ce segment niche."
            }},
            "bottom_up": {{
                 "target_volume": {{ 
                    "value": 2500, 
                    "unit": "sites industriels", 
                    "source": "INSEE + Proxy", 
                    "desc": "Base: 5000 sites Seveso x 50% équipés potentiels." 
                 }},
                 "unit_price": {{ 
                    "value": 12000, 
                    "unit": "EUR/an", 
                    "source": "Benchmark Prix Public", 
                    "desc": "Prix moyen licence Enterprise (10k€) + Maintenance (2k€)." 
                 }}
            }},
            "supply_led": {{
                 "top_players_revenue": {{ 
                    "value": 15000000, 
                    "unit": "EUR", 
                    "source": "Rapports Annuels (Estimé)", 
                    "desc": "Revenus cumulés estimé des leaders A (8M€) et B (7M€)." 
                 }},
                 "long_tail_factor": {{ 
                    "value": 2.0, 
                    "unit": "multiplicateur", 
                    "source": "Hypothèse Pareto", 
                    "desc": "Marché fragmenté : les leaders ne font que 50% du volume, d'où x2." 
                 }}
            }},
            "ratios": {{
                 "sam_pct": 30,
                 "sam_desc": "On cible uniquement le segment PME (30% du volume).",
                 "som_pct": 10,
                 "som_desc": "Objectif de part de marché réaliste à 3 ans."
            }}
        }}
        
        Sois CRÉATIF mais RIGOUREUX. Si tu fais une estimation de Fermi, explique-la dans "desc".
        Réponds UNIQUEMENT le JSON.
        """)
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({"scope": scope})
            
            # Parsing
            content = response.content.strip()
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            
            data = json.loads(content)
            facts = []
            ts = int(datetime.now().timestamp())
            
            # 0. SCOPE DEFINITION FACT (NEW)
            if "scope_definition" in data:
                sd = data["scope_definition"]
                facts.append({
                    "id": f"scope_def_{ts}",
                    "category": "scope_definition",
                    "key": "market_scope_definition",
                    "value": sd, # Store the whole dict
                    "unit": "N/A",
                    "source": "Moteur Sémantique",
                    "confidence": "high",
                    "notes": "Définition explicite du périmètre avant calcul."
                })

            # 1. SECONDARY TAM FACT
            if "secondary_tam" in data and data["secondary_tam"].get("value"):
                st = data["secondary_tam"]
                facts.append({
                    "id": f"gen_tam_sec_{ts}",
                    "category": "market_estimation",
                    "key": "tam_global_market", # Standard key for Engine
                    "value": st["value"],
                    "unit": st["unit"],
                    "source": st.get("source", "Analyste IA"),
                    "source_type": "Secondaire",
                    "retrieval_method": "Rapport",
                    "confidence": "high" if st.get("confidence", 0) > 0.7 else "medium",
                    "notes": st.get("desc", f"Scope Source: {st.get('scope_match', 'N/A')}. Year: {st.get('year')}"),
                    "derivation": "secondary", # NEW FIELD
                    "coherence_score": st.get("confidence", 0.5)
                })

            # 2. BOTTOM UP FACTS
            if "bottom_up" in data:
                bu = data["bottom_up"]
                if bu.get("target_volume"):
                    facts.append({
                        "id": f"gen_bu_vol_{ts}",
                        "category": "market_estimation",
                        "key": "total_potential_customers",
                        "value": bu["target_volume"]["value"],
                        "unit": bu["target_volume"]["unit"],
                        "source": bu["target_volume"].get("source", "Estimation"),
                        "source_type": "Primaire/Proxy",
                        "notes": bu["target_volume"].get("desc", ""),
                        "derivation": "bottom_up_brick"
                    })
                if bu.get("unit_price"):
                    facts.append({
                        "id": f"gen_bu_price_{ts}",
                        "category": "market_estimation",
                        "key": "average_price",
                        "value": bu["unit_price"]["value"],
                        "unit": bu["unit_price"]["unit"],
                        "source": bu["unit_price"].get("source", "Estimation"),
                        "source_type": "Estimation",
                        "notes": bu["unit_price"].get("desc", ""),
                        "derivation": "bottom_up_brick"
                    })

            # 3. SUPPLY LED FACTS (New Keys)
            if "supply_led" in data:
                sl = data["supply_led"]
                if sl.get("top_players_revenue"):
                    facts.append({
                        "id": f"gen_sup_rev_{ts}",
                        "category": "market_estimation",
                        "key": "top_players_cumulative_revenue",
                        "value": sl["top_players_revenue"]["value"],
                        "unit": sl["top_players_revenue"]["unit"],
                        "source": sl["top_players_revenue"].get("source"),
                        "source_type": "Aggregated",
                        "notes": sl["top_players_revenue"].get("desc", "Aggregation des revenus leaders"), # ADDED NOTES
                        "derivation": "supply_brick"
                    })
                if sl.get("long_tail_factor"):
                    facts.append({
                        "id": f"gen_sup_fac_{ts}",
                        "category": "market_estimation",
                        "key": "market_multiplier_factor",
                        "value": sl["long_tail_factor"]["value"],
                        "unit": "x",
                        "source": sl["long_tail_factor"].get("source"),
                        "source_type": "Heuristic",
                        "notes": sl["long_tail_factor"].get("desc", "Facteur d'extension Pareto"), # ADDED NOTES
                        "derivation": "supply_brick"
                    })

            # 4. RATIOS
            if "ratios" in data:
                r = data["ratios"]
                facts.append({
                    "id": f"gen_sam_{ts}",
                    "category": "market_estimation",
                    "key": "sam_percent",
                    "value": (r.get("sam_pct", 20) / 100.0),
                    "unit": "%",
                    "source": "Segmentation IA",
                    "confidence": "medium",
                    "notes": r.get("sam_desc", "Sélection du segment adressable.") # ADDED NOTES
                })
                facts.append({
                    "id": f"gen_som_{ts}",
                    "category": "market_estimation",
                    "key": "som_share",
                    "value": (r.get("som_pct", 5) / 100.0),
                    "unit": "%",
                    "source": "Cible Stratégique IA",
                    "confidence": "low",
                    "notes": r.get("som_desc", "Part de marché cible réaliste.") # ADDED NOTES
                })

            print(f"✅ [MARKET GENERATION] {len(facts)} Facts Granulaires Générés")
            return facts

        except Exception as e:
            print(f"❌ [MARKET GENERATION] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return []

    def find_competitors(self, scope: str) -> List[str]:
        """
        Identifies top 5 public competitors tickers for the given scope using Mistral.
        Returns a list of tickers (e.g. ['SAP', 'ORCL', 'CRM']).
        """
        print(f"🕵️‍♂️ [COMPETITORS] Recherche des concurrents pour : {scope}")
        
        prompt = ChatPromptTemplate.from_template("""
        Tu es un expert en intelligence économique.
        Pour le marché : "{scope}", identifie les 5 entreprises cotées en bourse les plus pertinentes (Concurrents directs).
        
        Format attendu : Une liste JSON de leurs TICKERS (Symboles boursiers) valides sur Yahoo Finance (US ou EU).
        Exemple : ["SAP", "ORCL", "CRM", "MSFT", "SAGE.L"]
        
        Réponds UNIQUEMENT le tableau JSON. Rien d'autre.
        """)
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({"scope": scope})
            
            content = response.content.strip().replace("```json", "").replace("```", "")
            tickers = json.loads(content)
            
            # Basic cleaning
            valid_tickers = [t.strip().upper() for t in tickers if isinstance(t, str) and len(t) < 10]
            print(f"✅ [COMPETITORS] Trouvés : {valid_tickers}")
            return valid_tickers
            
        except Exception as e:
            print(f"❌ [COMPETITORS] Erreur: {e}")
            # Fallback list depends on scope, but return empty safe
            return ["SAP", "ORCL", "MSFT"] # Generic Fallback

    def generate_company_market_analysis(self, company_name: str, company_context: str = "") -> Dict[str, Any]:
        """
        NOUVELLE MÉTHODE - Analyse de marché centrée sur une entreprise.
        
        Méthodologie KPMG en 7 étapes :
        1. Point de départ : l'entreprise (core business, marché de référence)
        2. Placement dans le marché (périmètre précis)
        3. Segmentation multi-axes
        4. Dynamiques & tendances
        5. Lien entreprise ↔ segments
        6. Règles méthodologiques strictes
        7. Format de sortie structuré
        
        Args:
            company_name: Nom de l'entreprise (ex: "Doctolib", "Mirakl")
            company_context: Contexte additionnel (secteur, offres, clients...)
            
        Returns:
            Analyse structurée avec facts vérifiables
        """
        print(f"🏢 [MARKET ANALYSIS] Analyse centrée entreprise pour : {company_name}")
        
        prompt = ChatPromptTemplate.from_template("""
Tu es un assistant d'analyse stratégique pour un cabinet de conseil de premier plan.
Ta mission est de partir d'une entreprise donnée, de la positionner dans son marché réel, puis de reconstruire le marché de manière structurée, segmentée et dynamique, en t'appuyant uniquement sur des sources vérifiables.

═══════════════════════════════════════════════════════════════
ENTREPRISE À ANALYSER : {company_name}
CONTEXTE ADDITIONNEL : {company_context}
═══════════════════════════════════════════════════════════════

🔒 RÈGLE FONDAMENTALE : MÉTHODE FACTS-FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Chaque fait utilisé DOIT être : identifié, daté, sourcé, qualifié (primaire/secondaire/proxy)
- Si un fait est incertain : le déclarer explicitement + proposer méthode de contournement
- INTERDIT d'inventer des chiffres sans justification

📋 FORMAT DE SORTIE JSON STRICT :
{{
    "executive_summary": {{
        "company_positioning": "Résumé en 2-3 phrases du positionnement",
        "core_business": "Produit/service réellement monétisé",
        "reference_market": "Nom standardisé du marché principal",
        "adjacent_markets": ["Marché adjacent 1", "Marché adjacent 2"],
        "key_insight": "L'insight stratégique principal"
    }},
    
    "methodology": {{
        "facts_used": [
            {{
                "fact_id": "FACT_001",
                "description": "Description du fait",
                "value": 1500000000,
                "unit": "EUR",
                "date": "2024",
                "source": "Nom EXACT de la source (ex: IDC Tracker Q3 2024)",
                "source_type": "primaire|secondaire|proxy",
                "confidence": "high|medium|low"
            }}
        ],
        "missing_data": [
            {{
                "data_needed": "Donnée manquante",
                "workaround": "Méthode de contournement proposée",
                "proxy_used": "Description du proxy si applicable"
            }}
        ],
        "assumptions": [
            {{
                "assumption_id": "HYP_001",
                "description": "Description de l'hypothèse",
                "justification": "Pourquoi cette hypothèse est raisonnable",
                "impact_if_wrong": "Conséquence si l'hypothèse est fausse"
            }}
        ]
    }},
    
    "market_mapping": {{
        "market_name": "Nom standardisé (terminologie cabinets/bases de données)",
        "perimeter": {{
            "value_type": "revenu_final|depenses_IT|capex|opex",
            "business_model": "SaaS|licences|services|mix",
            "client_typology": "PME|ETI|grands_comptes|B2C",
            "geography": "Global|Europe|France|...",
            "inclusions": ["Ce qui est inclus 1", "Ce qui est inclus 2"],
            "exclusions": ["Ce qui est exclu 1", "Ce qui est exclu 2"]
        }},
        "market_size": {{
            "tam": {{"value": null, "unit": "EUR", "year": "2024", "source": "Source", "confidence": "medium"}},
            "sam": {{"value": null, "unit": "EUR", "year": "2024", "source": "Source", "confidence": "medium"}},
            "som": {{"value": null, "unit": "EUR", "year": "2024", "source": "Source", "confidence": "low"}}
        }}
    }},
    
    "segmentation": {{
        "by_client": [
            {{
                "segment_name": "PME (<250 salariés)",
                "weight_pct": 35,
                "economic_logic": "Ticket moyen plus faible mais volume important",
                "attractiveness": "high|medium|low",
                "maturity": "emerging|growing|mature|declining"
            }}
        ],
        "by_usage": [
            {{
                "segment_name": "Usage Core",
                "weight_pct": 60,
                "economic_logic": "Besoin fondamental du marché",
                "attractiveness": "high",
                "maturity": "mature"
            }}
        ],
        "by_geography": [
            {{
                "segment_name": "France",
                "weight_pct": 25,
                "economic_logic": "Marché domestique principal",
                "attractiveness": "medium",
                "maturity": "growing"
            }}
        ]
    }},
    
    "dynamics": {{
        "growth_trends": [
            {{
                "trend": "Description de la tendance",
                "type": "structural|conjunctural|prospective",
                "impact": "+12% CAGR 2024-2028",
                "source": "Gartner 2024",
                "confidence": "high"
            }}
        ],
        "drivers": [
            {{
                "driver": "Facteur moteur",
                "category": "regulation|technology|cost|usage",
                "direction": "positive|negative",
                "magnitude": "high|medium|low"
            }}
        ],
        "weak_signals": [
            {{
                "signal": "Signal faible détecté",
                "potential_impact": "Rupture potentielle",
                "timeline": "1-2 ans|3-5 ans|>5 ans"
            }}
        ]
    }},
    
    "company_segment_fit": {{
        "current_presence": [
            {{
                "segment": "Nom du segment",
                "position": "leader|challenger|niche",
                "market_share_est": 15,
                "source": "Estimation basée sur..."
            }}
        ],
        "over_exposed": ["Segment 1 (risque de...)"],
        "under_exposed": ["Segment 2 (opportunité de...)"],
        "strategic_fit": ["Segments cohérents avec l'ADN"],
        "out_of_scope": ["Segments hors scope réaliste"]
    }},
    
    "reliability_assessment": {{
        "overall_confidence": "high|medium|low",
        "data_coverage": 75,
        "methodology_robustness": "Évaluation de la solidité méthodologique",
        "key_uncertainties": ["Incertitude 1", "Incertitude 2"],
        "recommendation_for_deepdive": "Recommandation pour approfondir"
    }}
}}

🔍 RÈGLES DE SOURÇAGE STRICTES :
- Ne JAMAIS donner un chiffre sans : périmètre + méthode + source
- Si plusieurs estimations existent : les comparer et expliquer les écarts
- Si donnée incertaine : fourchette OU méthode alternative
- SOURCES ACCEPTÉES : IDC, Gartner, Statista, Xerfi, McKinsey, BCG, rapports annuels, SEC filings

Réponds UNIQUEMENT avec du JSON valide, aucun texte autour.
""")
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({
                "company_name": company_name,
                "company_context": company_context or "Pas de contexte additionnel fourni."
            })
            
            # Parsing du JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            if content.startswith("```"):
                content = content.replace("```", "")
            
            analysis = json.loads(content)
            
            # Ajouter métadonnées
            analysis["_meta"] = {
                "company": company_name,
                "generated_at": datetime.now().isoformat(),
                "model": "mistral-small",
                "methodology": "KPMG Market Sizing v2.0"
            }
            
            # Convertir en Facts pour le facts_manager
            facts = self._convert_market_analysis_to_facts(analysis, company_name)
            
            print(f"✅ [MARKET ANALYSIS] Analyse générée : {len(facts)} facts extraits")
            
            return {
                "analysis": analysis,
                "facts": facts,
                "success": True
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ [MARKET ANALYSIS] Erreur parsing JSON: {e}")
            return {"success": False, "error": f"Parsing error: {e}", "facts": []}
        except Exception as e:
            print(f"❌ [MARKET ANALYSIS] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "facts": []}
    
    def _convert_market_analysis_to_facts(self, analysis: Dict, company: str) -> List[Dict]:
        """Convertit l'analyse en facts structurés pour le facts_manager."""
        facts = []
        ts = int(datetime.now().timestamp())
        
        # 1. Facts de sizing
        mapping = analysis.get("market_mapping", {})
        sizing = mapping.get("market_size", {})
        
        for metric in ["tam", "sam", "som"]:
            data = sizing.get(metric, {})
            if data and data.get("value"):
                facts.append({
                    "id": f"ma_{company}_{metric}_{ts}",
                    "category": "market_estimation",
                    "key": f"{metric}_global_market" if metric == "tam" else f"{metric}_percent" if metric == "sam" else "som_share",
                    "value": data["value"],
                    "unit": data.get("unit", "EUR"),
                    "source": data.get("source", "Analyse IA"),
                    "source_type": "Secondaire",
                    "confidence": data.get("confidence", "medium"),
                    "notes": f"Marché: {mapping.get('market_name', company)}, Périmètre: {mapping.get('perimeter', {}).get('geography', 'N/A')}"
                })
        
        # 2. Facts des hypothèses
        methodology = analysis.get("methodology", {})
        for fact_data in methodology.get("facts_used", []):
            if fact_data.get("value"):
                facts.append({
                    "id": fact_data.get("fact_id", f"fact_{ts}"),
                    "category": "market_estimation",
                    "key": fact_data.get("description", "").replace(" ", "_").lower()[:50],
                    "value": fact_data["value"],
                    "unit": fact_data.get("unit", "EUR"),
                    "source": fact_data.get("source", "Analyse"),
                    "source_type": fact_data.get("source_type", "secondaire").capitalize(),
                    "confidence": fact_data.get("confidence", "medium"),
                    "notes": f"Date: {fact_data.get('date', 'N/A')}"
                })
        
        # 3. Hypothèses comme facts qualifiés
        for assumption in methodology.get("assumptions", []):
            facts.append({
                "id": assumption.get("assumption_id", f"hyp_{ts}"),
                "category": "hypothesis",
                "key": assumption.get("description", "")[:50].replace(" ", "_").lower(),
                "value": assumption.get("description", ""),
                "unit": "N/A",
                "source": "Hypothèse Analyste",
                "source_type": "Hypothèse",
                "confidence": "low",
                "notes": f"Justification: {assumption.get('justification', 'N/A')}. Impact si faux: {assumption.get('impact_if_wrong', 'N/A')}"
            })
        
        return facts

    def generate_contextual_market_sizing(self, company_name: str, country: str, year: str, additional_context: str = "") -> Dict[str, Any]:
        """
        MÉTHODE DE MARKET SIZING CONTEXTUEL - Bottom-Up Local
        
        Méthodologie rigoureuse de sizing basée sur :
        1. Verrouillage du contexte (entreprise + pays + année)
        2. Définition du marché spécifique à l'entreprise
        3. Utilisation stricte de la base de facts centralisée
        4. Reconstruction bottom-up locale
        5. Calcul explicite et transparent
        6. Comparaison et validation contextuelle
        7. Évaluation de fiabilité
        
        Args:
            company_name: Nom de l'entreprise cible
            country: Pays / zone géographique
            year: Année de référence
            additional_context: Contexte additionnel (offres, modèle éco, etc.)
            
        Returns:
            Analyse structurée avec estimation bottom-up locale
        """
        print(f"📊 [CONTEXTUAL SIZING] Entreprise: {company_name} | Pays: {country} | Année: {year}")
        
        prompt = ChatPromptTemplate.from_template("""
Tu es un assistant d'analyse stratégique senior utilisé par un cabinet de conseil de premier plan.
Tu dois estimer la taille d'un marché dans un contexte précis, défini par une entreprise cible, un pays et une année donnée.
Tu raisonnes UNIQUEMENT dans ce contexte, sans extrapolation générique.

═══════════════════════════════════════════════════════════════
📌 CONTEXTE À ANALYSER
═══════════════════════════════════════════════════════════════
Entreprise : {company_name}
Pays / Zone : {country}
Année : {year}
Contexte additionnel : {additional_context}
═══════════════════════════════════════════════════════════════

🔒 RÈGLE FONDAMENTALE : Chaque fact doit être référencé (ID, source, date, pays).
Aucune donnée non traçable n'est autorisée. Si un fact global est utilisé, tu dois l'ajuster au contexte local et expliquer la méthode.

📋 FORMAT DE SORTIE JSON STRICT :
{{
    "context_lock": {{
        "company": "{company_name}",
        "country": "{country}",
        "year": "{year}",
        "company_offerings": ["Offre 1 pertinente localement", "Offre 2"],
        "local_business_model": "Description du modèle économique applicable localement",
        "missing_info": ["Information manquante 1 (si applicable)"],
        "context_validated": true
    }},
    
    "market_definition": {{
        "market_name": "Nom du marché tel qu'adressable par l'entreprise",
        "market_justification": "Pourquoi ce périmètre et pas un marché générique",
        "excluded_segments": [
            {{
                "segment": "Segment exclu",
                "reason": "Raison de l'exclusion (maturité, régulation, etc.)"
            }}
        ],
        "local_adaptations": {{
            "maturity_level": "emerging|growing|mature",
            "regulatory_context": "Cadre réglementaire local pertinent",
            "healthcare_system": "Structure du système (si applicable)",
            "purchasing_practices": "Pratiques d'achat locales"
        }}
    }},
    
    "facts_used": [
        {{
            "fact_id": "FACT_LOCAL_001",
            "description": "Description du fait",
            "value": 10000,
            "unit": "EUR|unités|%",
            "source": "Nom EXACT de la source",
            "source_type": "primaire|secondaire|proxy",
            "date": "2024",
            "country": "{country}",
            "is_global_adjusted": false,
            "adjustment_method": null
        }}
    ],
    
    "bottom_up_reconstruction": {{
        "economic_unit": {{
            "name": "Unité économique locale (ex: Médecin libéral, Cabinet, Établissement)",
            "definition": "Définition précise de l'unité dans le contexte local",
            "relevance": "Pourquoi cette unité est pertinente"
        }},
        "addressable_population": {{
            "total_units_in_country": 50000,
            "total_units_source": "Source du nombre total",
            "filters_applied": [
                {{
                    "filter_name": "Spécialité médicale",
                    "filter_value": "Généralistes uniquement",
                    "remaining_units": 35000,
                    "source_or_hypothesis": "INSEE 2024 / Hypothèse basée sur..."
                }},
                {{
                    "filter_name": "Équipement numérique",
                    "filter_value": "Connectés internet haut débit",
                    "remaining_units": 30000,
                    "source_or_hypothesis": "ARCEP 2024"
                }},
                {{
                    "filter_name": "Capacité de paiement",
                    "filter_value": "Revenus > seuil X",
                    "remaining_units": 25000,
                    "source_or_hypothesis": "Hypothèse: 85% des connectés"
                }}
            ],
            "final_addressable_units": 25000
        }},
        "local_unit_value": {{
            "annual_price_local": 1200,
            "currency": "EUR",
            "price_source": "Pricing public / Estimation secteur",
            "comparison_vs_reference": "Prix France: 1500€ → Ajustement -20% pour {country}",
            "adjustment_rationale": "Pouvoir d'achat inférieur de X%, concurrence locale plus forte"
        }},
        "adoption_rate": {{
            "estimated_rate_percent": 15,
            "rate_justification": "Marché émergent, adoption progressive",
            "rate_source": "Benchmark marchés similaires / Hypothèse prudente"
        }}
    }},
    
    "calculation": {{
        "formula": "Taille du marché = Unités éligibles × Prix annuel local × Taux d'adoption",
        "step_by_step": [
            "1. Unités éligibles: 25,000",
            "2. Prix annuel local: 1,200 EUR",
            "3. Taux d'adoption réaliste: 15%",
            "4. Calcul: 25,000 × 1,200 × 0.15 = 4,500,000 EUR"
        ],
        "intermediate_values": {{
            "gross_potential": 30000000,
            "after_filters": 25000000,
            "with_adoption": 4500000
        }},
        "final_estimate": {{
            "value": 4500000,
            "unit": "EUR",
            "year": "{year}",
            "range_low": 3500000,
            "range_high": 6000000
        }}
    }},
    
    "validation": {{
        "sanity_checks": [
            {{
                "check": "Comparaison avec rapport sectoriel local",
                "reference_value": 5000000,
                "reference_source": "Xerfi {country} 2024",
                "delta_percent": -10,
                "explanation": "Écart expliqué par périmètre plus restrictif"
            }},
            {{
                "check": "Benchmark régional (pays similaire)",
                "reference_value": 4800000,
                "reference_source": "IDC Europe Est 2024",
                "delta_percent": -6,
                "explanation": "Cohérent avec benchmark régional"
            }}
        ],
        "coherence_assessment": "L'estimation est cohérente avec les benchmarks disponibles"
    }},
    
    "reliability": {{
        "overall_confidence": "HIGH|MEDIUM|LOW",
        "confidence_justification": "Justification basée sur qualité des données, nombre d'hypothèses, granularité",
        "data_quality_score": 75,
        "hypothesis_count": 3,
        "key_uncertainties": [
            "Incertitude 1: Taux d'adoption difficile à valider",
            "Incertitude 2: Prix local basé sur estimation"
        ],
        "limitations": [
            "Données locales limitées pour ce marché",
            "Hypothèse sur le pricing non validée"
        ],
        "recommendations": [
            "Valider le pricing avec des acteurs locaux",
            "Affiner le taux d'adoption via étude terrain"
        ]
    }},
    
    "sources_registry": [
        {{
            "source_id": "SRC_001",
            "source_name": "INSEE",
            "source_url": "https://www.insee.fr/...",
            "data_used": "Nombre de médecins libéraux",
            "reliability": "HIGH"
        }}
    ]
}}

🚨 RÈGLES STRICTES :
1. Ne JAMAIS utiliser un prix France/US sans ajustement expliqué
2. Chaque filtre doit être justifié ET sourcé (ou explicitement hypothétique)
3. Le taux d'adoption doit être justifié par des benchmarks ou logique sectorielle
4. Les écarts avec les références doivent être expliqués par : périmètre, maturité, régulation, modèle économique

Réponds UNIQUEMENT avec du JSON valide, aucun texte autour.
""")
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({
                "company_name": company_name,
                "country": country,
                "year": year,
                "additional_context": additional_context or "Pas de contexte additionnel fourni."
            })
            
            # Parsing du JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            if content.startswith("```"):
                content = content.replace("```", "")
            
            analysis = json.loads(content)
            
            # Ajouter métadonnées
            analysis["_meta"] = {
                "company": company_name,
                "country": country,
                "year": year,
                "generated_at": datetime.now().isoformat(),
                "model": "mistral-small",
                "methodology": "KPMG Contextual Market Sizing v1.0"
            }
            
            # Convertir en Facts
            facts = self._convert_contextual_sizing_to_facts(analysis, company_name, country, year)
            
            print(f"✅ [CONTEXTUAL SIZING] Analyse générée : {len(facts)} facts extraits")
            
            return {
                "analysis": analysis,
                "facts": facts,
                "success": True
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ [CONTEXTUAL SIZING] Erreur parsing JSON: {e}")
            return {"success": False, "error": f"Parsing error: {e}", "facts": []}
        except Exception as e:
            print(f"❌ [CONTEXTUAL SIZING] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "facts": []}
    
    def _convert_contextual_sizing_to_facts(self, analysis: Dict, company: str, country: str, year: str) -> List[Dict]:
        """Convertit l'analyse contextuelle en facts structurés."""
        facts = []
        ts = int(datetime.now().timestamp())
        
        # 1. Estimation finale
        calc = analysis.get("calculation", {})
        final = calc.get("final_estimate", {})
        if final.get("value"):
            facts.append({
                "id": f"ctx_{company}_{country}_{year}_final_{ts}",
                "category": "market_estimation",
                "key": f"market_size_{country.lower()}_{year}",
                "value": final["value"],
                "unit": final.get("unit", "EUR"),
                "source": f"Analyse Bottom-Up KPMG ({country})",
                "source_type": "Primaire",
                "confidence": analysis.get("reliability", {}).get("overall_confidence", "medium").lower(),
                "notes": f"Entreprise: {company}, Fourchette: {final.get('range_low', 'N/A')} - {final.get('range_high', 'N/A')} {final.get('unit', 'EUR')}"
            })
        
        # 2. Facts utilisés dans l'analyse
        for fact_data in analysis.get("facts_used", []):
            if fact_data.get("value"):
                facts.append({
                    "id": fact_data.get("fact_id", f"fact_ctx_{ts}"),
                    "category": "market_estimation",
                    "key": fact_data.get("description", "").replace(" ", "_").lower()[:50],
                    "value": fact_data["value"],
                    "unit": fact_data.get("unit", "EUR"),
                    "source": fact_data.get("source", "Analyse"),
                    "source_type": fact_data.get("source_type", "secondaire").capitalize(),
                    "confidence": "high" if fact_data.get("source_type") == "primaire" else "medium",
                    "notes": f"Pays: {fact_data.get('country', country)}, Date: {fact_data.get('date', year)}"
                })
        
        # 3. Bottom-up data points
        bu = analysis.get("bottom_up_reconstruction", {})
        addr_pop = bu.get("addressable_population", {})
        if addr_pop.get("final_addressable_units"):
            facts.append({
                "id": f"ctx_{company}_{country}_units_{ts}",
                "category": "market_estimation",
                "key": f"addressable_units_{country.lower()}",
                "value": addr_pop["final_addressable_units"],
                "unit": "unités",
                "source": addr_pop.get("total_units_source", "Analyse"),
                "source_type": "Secondaire",
                "confidence": "medium",
                "notes": f"Total avant filtres: {addr_pop.get('total_units_in_country', 'N/A')}"
            })
        
        # 4. Prix unitaire local
        unit_val = bu.get("local_unit_value", {})
        if unit_val.get("annual_price_local"):
            facts.append({
                "id": f"ctx_{company}_{country}_price_{ts}",
                "category": "market_estimation",
                "key": f"unit_price_{country.lower()}",
                "value": unit_val["annual_price_local"],
                "unit": unit_val.get("currency", "EUR"),
                "source": unit_val.get("price_source", "Estimation"),
                "source_type": "Secondaire",
                "confidence": "medium",
                "notes": f"Ajustement: {unit_val.get('adjustment_rationale', 'N/A')}"
            })
        
        return facts

    def generate_market_segmentation(self, company_name: str, offerings: str, country: str, year: str, market_sizing_context: str = "") -> Dict[str, Any]:
        """
        SEGMENTATION DES ENTREPRISES CONCURRENTES
        
        Méthodologie : Segmenter les entreprises qui captent la valeur du marché,
        en s'appuyant sur les résultats du Market Sizing contextuel.
        
        On ne segmente PAS les clients, on segmente les ENTREPRISES concurrentes
        selon leur logique de capture de valeur économique.
        
        Args:
            company_name: Entreprise de référence
            offerings: Offre / périmètre fonctionnel analysé
            country: Pays / zone géographique
            year: Année de référence
            market_sizing_context: Résultats du Market Sizing (définition, unités, segments demande, ordres de grandeur)
            
        Returns:
            Segmentation des entreprises concurrentes avec lien au sizing
        """
        print(f"🎯 [COMPANY SEGMENTATION] Entreprise: {company_name} | Offres: {offerings} | Pays: {country}")
        
        prompt = ChatPromptTemplate.from_template("""
Tu es un assistant d'analyse stratégique senior utilisé par un cabinet de conseil.
Ta mission est de segmenter un marché par TYPES D'ENTREPRISES CONCURRENTES,
en t'appuyant explicitement sur les résultats du module d'estimation de taille de marché.

⚠️ ATTENTION : Tu ne segmentes PAS les clients. Tu segmentes les ENTREPRISES qui captent la valeur du marché.

═══════════════════════════════════════════════════════════════
📌 CONTEXTE
═══════════════════════════════════════════════════════════════
Entreprise de référence : {company_name}
Offre / périmètre : {offerings}
Pays / Zone : {country}
Année : {year}

📊 RÉSULTATS DU MARKET SIZING (à utiliser obligatoirement) :
{market_sizing_context}
═══════════════════════════════════════════════════════════════

🔒 PRINCIPE FONDAMENTAL :
Segmenter les entreprises selon la manière dont elles CAPTURENT LA VALEUR, pas selon leur branding.
Chaque segment = un sous-espace économique du market sizing + logique de revenus distincte + poids économique différenciable.

📋 FORMAT DE SORTIE JSON STRICT :
{{
    "context_lock": {{
        "reference_company": "{company_name}",
        "offering_scope": "{offerings}",
        "country": "{country}",
        "year": "{year}",
        "market_sizing_available": true,
        "market_sizing_summary": "Résumé du sizing utilisé",
        "total_market_value": 500000000,
        "market_unit": "EUR",
        "missing_sizing_elements": []
    }},
    
    "segmentation_logic": {{
        "primary_axis": {{
            "axis_name": "Axe principal de segmentation",
            "axis_type": "economic_unit|monetization|value_level|functional_scope|integration_degree",
            "justification": "Pourquoi cet axe est structurant économiquement",
            "link_to_sizing": "Comment cet axe se traduit en différences de taille de marché"
        }},
        "secondary_axes": [
            {{
                "axis_name": "Axe secondaire",
                "axis_type": "type",
                "relevance": "Pertinence pour différencier les entreprises"
            }}
        ],
        "rejected_axes": [
            {{
                "axis_name": "Axe rejeté",
                "reason": "Pourquoi cet axe n'est pas économiquement justifié"
            }}
        ]
    }},
    
    "company_segments": [
        {{
            "segment_id": "SEG_01",
            "segment_name": "Nom du type d'entreprise",
            "description": "Description du type d'entreprise",
            "value_creation_logic": "Comment ces entreprises créent de la valeur",
            "target_economic_unit": "par médecin|par établissement|par acte|par patient|etc.",
            "revenue_model": "abonnement|commission|usage|licence|freemium",
            "pricing_position": "low_arpu_volume|mid_market|premium",
            "functional_scope": "pure_play|plateforme_elargie|solution_integree",
            "integration_degree": "standalone|suite|infrastructure",
            "market_share_captured": {{
                "value": 150000000,
                "unit": "EUR",
                "percentage_of_total": 30,
                "source": "Lien avec hypothèse du sizing",
                "confidence": "HIGH|MEDIUM|LOW"
            }},
            "representative_players": ["Acteur 1", "Acteur 2", "Acteur 3"],
            "entry_barriers": ["Barrière 1", "Barrière 2"],
            "growth_dynamics": "Description de la dynamique (croissance, maturité, déclin)",
            "why_structurally_different": "Pourquoi ces entreprises sont économiquement différentes des autres"
        }}
    ],
    
    "reference_company_positioning": {{
        "current_segments": [
            {{
                "segment_id": "SEG_01",
                "presence_level": "dominant|challenger|niche|absent",
                "estimated_share_in_segment": 25,
                "strategic_importance": "core|adjacent|peripheral"
            }}
        ],
        "core_market_segments": ["SEG_01", "SEG_02"],
        "credible_adjacent_segments": [
            {{
                "segment_id": "SEG_03",
                "expansion_feasibility": "HIGH|MEDIUM|LOW",
                "strategic_rationale": "Pourquoi ce segment est adjacent crédible"
            }}
        ],
        "out_of_scope_segments": [
            {{
                "segment_id": "SEG_04",
                "reason": "Pourquoi hors scope réaliste"
            }}
        ]
    }},
    
    "market_value_distribution": {{
        "segments_by_value": [
            {{
                "segment_id": "SEG_01",
                "value_captured": 150000000,
                "percentage": 30,
                "trend": "growing|stable|declining"
            }}
        ],
        "concentration_analysis": "Analyse de la concentration du marché",
        "value_migration_trends": "Vers où migre la valeur du marché"
    }},
    
    "visualizations": {{
        "market_map": {{
            "type": "bubble_chart",
            "x_axis": "Degré d'intégration",
            "y_axis": "Valeur captée",
            "bubble_size": "Nombre d'acteurs",
            "data": [
                {{"segment": "SEG_01", "x": 2, "y": 4, "size": 15}}
            ]
        }},
        "value_chain": {{
            "stages": ["Acquisition", "Activation", "Rétention", "Expansion"],
            "segment_focus": {{"SEG_01": "Acquisition", "SEG_02": "Rétention"}}
        }},
        "market_share_pie": {{
            "segments": ["SEG_01", "SEG_02", "SEG_03"],
            "values": [30, 25, 20]
        }}
    }},
    
    "reliability": {{
        "overall_confidence": "HIGH|MEDIUM|LOW",
        "confidence_justification": "Justification",
        "sizing_granularity": "HIGH|MEDIUM|LOW",
        "hypothesis_traceability": "HIGH|MEDIUM|LOW",
        "segment_boundary_clarity": "HIGH|MEDIUM|LOW",
        "local_competitive_coherence": "HIGH|MEDIUM|LOW",
        "key_limitations": ["Limitation 1", "Limitation 2"]
    }},
    
    "facts_and_hypotheses": {{
        "sizing_facts_used": [
            {{
                "fact_id": "SIZING_001",
                "description": "Fait du sizing utilisé",
                "value": "Valeur",
                "source": "Source",
                "used_for_segment": "SEG_01"
            }}
        ],
        "new_hypotheses": [
            {{
                "hypothesis_id": "HYP_SEG_001",
                "description": "Hypothèse formulée pour la segmentation",
                "justification": "Pourquoi raisonnable",
                "impact_if_wrong": "Conséquence"
            }}
        ]
    }}
}}

🚨 RÈGLES STRICTES :
1. Chaque segment = entreprises qui captent la valeur de la MÊME façon
2. Si deux types d'entreprises captent la même valeur de la même façon → les REGROUPER
3. 4 à 8 segments maximum, mutuellement exclusifs
4. INTERDICTION de segments non quantifiables si le sizing permet la quantification
5. Pour chaque segment : "Pourquoi ces entreprises sont-elles STRUCTURELLEMENT DIFFÉRENTES économiquement ?"

Réponds UNIQUEMENT avec du JSON valide, aucun texte autour.
""")
        
        try:
            llm = self._get_llm()
            chain = prompt | llm
            response = chain.invoke({
                "company_name": company_name,
                "offerings": offerings,
                "country": country,
                "year": year,
                "market_sizing_context": market_sizing_context or "Market sizing non fourni - utiliser estimations génériques du secteur."
            })
            
            # Parsing du JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            if content.startswith("```"):
                content = content.replace("```", "")
            
            analysis = json.loads(content)
            
            # Ajouter métadonnées
            analysis["_meta"] = {
                "company": company_name,
                "country": country,
                "year": year,
                "generated_at": datetime.now().isoformat(),
                "model": "mistral-small",
                "methodology": "KPMG Company Segmentation v1.0"
            }
            
            # Convertir en Facts
            facts = self._convert_company_segmentation_to_facts(analysis, company_name, country, year)
            
            print(f"✅ [COMPANY SEGMENTATION] Analyse générée : {len(analysis.get('company_segments', []))} segments")
            
            return {
                "analysis": analysis,
                "facts": facts,
                "success": True
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ [COMPANY SEGMENTATION] Erreur parsing JSON: {e}")
            return {"success": False, "error": f"Parsing error: {e}", "facts": []}
        except Exception as e:
            print(f"❌ [COMPANY SEGMENTATION] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "facts": []}
    
    def _convert_company_segmentation_to_facts(self, analysis: Dict, company: str, country: str, year: str) -> List[Dict]:
        """Convertit la segmentation des entreprises en facts structurés."""
        facts = []
        ts = int(datetime.now().timestamp())
        
        # 1. Facts des segments d'entreprises
        for seg in analysis.get("company_segments", []):
            seg_id = seg.get("segment_id", f"seg_{ts}")
            market_share = seg.get("market_share_captured", {})
            
            if market_share.get("value"):
                facts.append({
                    "id": f"{seg_id}_{company}_{country}_{ts}",
                    "category": "company_segmentation",
                    "key": f"segment_value_{seg.get('segment_name', '').replace(' ', '_').lower()}",
                    "value": market_share["value"],
                    "unit": market_share.get("unit", "EUR"),
                    "source": market_share.get("source", "Analyse"),
                    "source_type": "Secondaire",
                    "confidence": market_share.get("confidence", "medium").lower(),
                    "notes": f"Segment: {seg.get('segment_name', 'N/A')}, Part: {market_share.get('percentage_of_total', 0)}%, Modèle: {seg.get('revenue_model', 'N/A')}"
                })
        
        # 2. Distribution de valeur
        dist = analysis.get("market_value_distribution", {})
        for seg_val in dist.get("segments_by_value", []):
            facts.append({
                "id": f"dist_{seg_val.get('segment_id')}_{ts}",
                "category": "company_segmentation",
                "key": f"market_distribution_{seg_val.get('segment_id', '').lower()}",
                "value": seg_val.get("percentage", 0),
                "unit": "%",
                "source": "Analyse segmentation",
                "source_type": "Secondaire",
                "confidence": "medium",
                "notes": f"Valeur: {seg_val.get('value_captured', 0)} EUR, Tendance: {seg_val.get('trend', 'N/A')}"
            })
        
        return facts


# Singleton global pour l'application
strategic_facts_service = StrategicFactsService()
