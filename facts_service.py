"""
FACTS Service - Financial Analytics Centralized Tracking System
================================================================

Ce module centralise la récupération des données financières pour éviter
les appels API redondants et garantir la cohérence des données.

Architecture:
- Singleton FinancialFactsService avec cache en mémoire
- Récupération unique par ticker
- Données pré-structurées pour les visualisations

Usage:
    from facts_service import facts_service
    facts = facts_service.get_company_facts("AAPL")
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time


class FinancialFactsService:
    """
    Service centralisé de récupération des données financières.
    Implémente un cache en mémoire pour optimiser les performances.
    """
    
    def __init__(self, cache_ttl_minutes: int = 15):
        """
        Initialise le service FACTS.
        
        Args:
            cache_ttl_minutes: Durée de vie du cache en minutes (défaut: 15)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
    
    def _is_cache_valid(self, ticker: str) -> bool:
        """Vérifie si le cache est encore valide pour un ticker."""
        if ticker not in self._cache_timestamps:
            return False
        return datetime.now() - self._cache_timestamps[ticker] < self._cache_ttl
    
    def get_company_facts(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """
        Récupère toutes les données financières pour un ticker.
        
        Args:
            ticker: Symbole boursier (ex: "AAPL", "MSFT")
            period: Période pour l'historique des cours
            
        Returns:
            Dictionnaire contenant toutes les données financières:
            - history: Historique des cours
            - financials: États financiers
            - balance_sheet: Bilan comptable
            - cashflow: Flux de trésorerie
            - info: Informations générales
        """
        cache_key = f"{ticker}_{period}"
        
        # Vérifier le cache
        if cache_key in self._cache and self._is_cache_valid(cache_key):
            print(f"📦 [FACTS] Cache hit pour {ticker}")
            return self._cache[cache_key]
        
        print(f"🔄 [FACTS] Récupération des données pour {ticker}...")
        
        try:
            stock = yf.Ticker(ticker)
            
            # Récupération avec gestion d'erreurs pour chaque composant
            facts = {
                "ticker": ticker,
                "period": period,
                "retrieved_at": datetime.now().isoformat(),
                "history": self._safe_get(lambda: stock.history(period=period)),
                "financials": self._safe_get(lambda: stock.financials),
                "balance_sheet": self._safe_get(lambda: stock.balance_sheet),
                "cashflow": self._safe_get(lambda: stock.cashflow),
                "info": self._safe_get(lambda: stock.info, default={}),
            }
            
            # Calculs dérivés pré-calculés pour optimiser les visualisations
            facts["derived"] = self._compute_derived_metrics(facts)
            
            # Mise en cache
            self._cache[cache_key] = facts
            self._cache_timestamps[cache_key] = datetime.now()
            
            print(f"✅ [FACTS] Données récupérées et mises en cache pour {ticker}")
            return facts
            
        except Exception as e:
            print(f"❌ [FACTS] Erreur pour {ticker}: {e}")
            return self._empty_facts(ticker, period, str(e))
    
    def _safe_get(self, func, default=None):
        """Exécute une fonction de récupération avec gestion d'erreur."""
        try:
            result = func()
            # Petit délai pour éviter le rate limiting
            time.sleep(0.1)
            return result
        except Exception as e:
            print(f"   ⚠️ Erreur partielle: {e}")
            return default if default is not None else pd.DataFrame()
    
    def _compute_derived_metrics(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule les métriques dérivées à partir des données brutes.
        Ces calculs sont effectués une seule fois lors du chargement.
        """
        derived = {}
        
        try:
            financials = facts.get("financials")
            balance_sheet = facts.get("balance_sheet")
            cashflow = facts.get("cashflow")
            
            if financials is not None and not financials.empty:
                financials_t = financials.T.sort_index()
                
                # Revenus et bénéfices
                revenue = financials_t.get('Total Revenue', financials_t.get('Revenue'))
                net_income = financials_t.get('Net Income', financials_t.get('Net Income Common Stockholders'))
                
                if revenue is not None:
                    derived["revenue"] = revenue
                if net_income is not None:
                    derived["net_income"] = net_income
                
                # Marge nette
                if revenue is not None and net_income is not None:
                    derived["net_margin"] = (net_income / revenue) * 100
            
            if balance_sheet is not None and not balance_sheet.empty:
                bs_t = balance_sheet.T.sort_index()
                
                # Actifs et passifs
                derived["total_assets"] = bs_t.get('Total Assets')
                derived["total_liabilities"] = bs_t.get('Total Liabilities Net Minority Interest', bs_t.get('Total Liabilities'))
                derived["stockholders_equity"] = bs_t.get('Stockholders Equity')
                derived["total_debt"] = bs_t.get('Total Debt', bs_t.get('Long Term Debt'))
                
                # Ratio Debt/Equity
                if derived.get("total_debt") is not None and derived.get("stockholders_equity") is not None:
                    derived["debt_to_equity"] = derived["total_debt"] / derived["stockholders_equity"]
                
                # ROE et ROA
                if "net_income" in derived:
                    if derived.get("stockholders_equity") is not None:
                        derived["roe"] = (derived["net_income"] / derived["stockholders_equity"]) * 100
                    if derived.get("total_assets") is not None:
                        derived["roa"] = (derived["net_income"] / derived["total_assets"]) * 100
            
            if cashflow is not None and not cashflow.empty:
                cf_t = cashflow.T.sort_index()
                
                # Free Cash Flow
                fcf = cf_t.get('Free Cash Flow')
                if fcf is None:
                    op_cf = cf_t.get('Total Cash From Operating Activities', cf_t.get('Operating Cash Flow'))
                    capex = cf_t.get('Capital Expenditures')
                    if op_cf is not None and capex is not None:
                        fcf = op_cf + capex
                derived["fcf"] = fcf
                
        except Exception as e:
            print(f"   ⚠️ Erreur calcul métriques dérivées: {e}")
        
        return derived
    
    def _empty_facts(self, ticker: str, period: str, error: str) -> Dict[str, Any]:
        """Retourne une structure vide en cas d'erreur."""
        return {
            "ticker": ticker,
            "period": period,
            "retrieved_at": datetime.now().isoformat(),
            "error": error,
            "history": pd.DataFrame(),
            "financials": pd.DataFrame(),
            "balance_sheet": pd.DataFrame(),
            "cashflow": pd.DataFrame(),
            "info": {},
            "derived": {}
        }
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        Vide le cache.
        
        Args:
            ticker: Si spécifié, vide uniquement le cache de ce ticker.
                   Sinon, vide tout le cache.
        """
        if ticker:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(ticker)]
            for key in keys_to_remove:
                del self._cache[key]
                del self._cache_timestamps[key]
            print(f"🗑️ [FACTS] Cache vidé pour {ticker}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            print("🗑️ [FACTS] Cache entièrement vidé")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        return {
            "entries": len(self._cache),
            "tickers": list(set(k.split("_")[0] for k in self._cache.keys())),
            "ttl_minutes": self._cache_ttl.total_seconds() / 60
        }


# Singleton global pour l'application
facts_service = FinancialFactsService()
