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
from typing import Dict, Any, Optional

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


# Singleton global pour l'application
strategic_facts_service = StrategicFactsService()
