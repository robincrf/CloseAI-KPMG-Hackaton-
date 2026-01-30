
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import json
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import textwrap

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# HELPER: GÉNÉRATION D'INSIGHTS
# ═══════════════════════════════════════════════════════════════

def generate_financial_insight(metric_name: str, data_series: pd.Series) -> dict:
    """
    Analyse une série temporelle simple et génère un insight court + fiabilité.
    Utilise des heuristiques statistiques pour la rapidité.
    
    Returns:
        {"insight": str, "reliability": str}
    """
    if data_series is None or data_series.empty:
        return {"insight": "Pas de données suffisantes pour l'analyse.", "reliability": "N/A"}

    # 1. Calcul de Tendance (CAGR simplifié ou Variation Totale)
    try:
        start_val = data_series.iloc[0]
        end_val = data_series.iloc[-1]
        
        if start_val == 0 or pd.isna(start_val) or pd.isna(end_val):
            change_pct = 0
        else:
            change_pct = ((end_val - start_val) / abs(start_val)) * 100
            
        if pd.isna(change_pct): change_pct = 0

            
        trend = "stable"
        if change_pct > 10: trend = "en hausse significative"
        elif change_pct > 2: trend = "en légère hausse"
        elif change_pct < -10: trend = "en baisse significative"
        elif change_pct < -2: trend = "en légère baisse"
        
        # 2. Détection Volatilité (Écart-type / Moyenne)
        mean_val = data_series.mean()
        std_val = data_series.std()
        
        volatility = "faible"
        if mean_val != 0:
            coef_var = std_val / abs(mean_val)
            if coef_var > 0.5: volatility = "élevée"
            elif coef_var > 0.2: volatility = "modérée"
            
        insight = f"Tendance **{trend}** ({change_pct:+.1f}%) sur la période. Volatilité {volatility}."
        
        # 3. Score de Fiabilité (Basé sur la complétude et régularité)
        # Pour l'instant on met une fiabilité basée sur le nombre de points
        nb_points = len(data_series)
        reliability_score = 100
        if nb_points < 3: reliability_score = 50
        if volatility == "élevée": reliability_score -= 20
        
        reliability = f"Fiabilité: {max(0, reliability_score)}%"
        
        return {"insight": insight, "reliability": reliability}
        
    except Exception as e:
        return {"insight": "Analyse automatique indisponible.", "reliability": "N/A"}

# ═══════════════════════════════════════════════════════════════
# SECTION 1 : VISUALISATIONS FINANCIÈRES
# ═══════════════════════════════════════════════════════════════

def plot_solvency_ratios(ticker_symbol: str) -> dict:
    """Génère un graphique de Solvabilité (Debt to Equity)"""
    try:
        stock = yf.Ticker(ticker_symbol)
        bs = stock.balance_sheet.T.sort_index() # Bilan
        
        err_result = {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        if bs.empty:
            return err_result
            
        years = bs.index.strftime('%Y')
        total_debt = bs.get('Total Debt', bs.get('Long Term Debt'))
        stockholders_equity = bs.get('Stockholders Equity', bs.get('Total Stockholder Equity'))
        
        if total_debt is not None and stockholders_equity is not None:
            # Ratio Debt-to-Equity
            de_ratio = total_debt / stockholders_equity
            
            # Insight
            analysis = generate_financial_insight("Ratio Dette/Equity", de_ratio)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=years,
                y=de_ratio,
                name='Debt to Equity Ratio',
                marker_color='#F68D2E' # KPMG Orange equivalent for alert/neutral
            ))
            
            fig.update_layout(
                title=dict(text=f"<b>SOLVABILITÉ (Debt/Equity)</b>", font=dict(color="#FFFFFF", size=18)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=40, r=20, t=60, b=30),
                shapes=[dict(type="line", x0=years[0], y0=2.0, x1=years[-1], y1=2.0, line=dict(color="#FF3D00", width=2, dash="dash"))],
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
            )
            return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        else:
            return err_result
            
    except Exception as e:
        return {"fig": go.Figure().add_annotation(text=f"Erreur: {e}", showarrow=False), "insight": "Erreur", "reliability": "0%"}

def plot_returns(ticker_symbol: str) -> dict:
    """Affiche ROE (Return on Equity) et ROA (Return on Assets)"""
    try:
        stock = yf.Ticker(ticker_symbol)
        financials = stock.financials.T.sort_index()
        bs = stock.balance_sheet.T.sort_index()
        
        err_result = {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}

        if financials.empty or bs.empty: return err_result

        years = financials.index.strftime('%Y')
        net_income = financials.get('Net Income', financials.get('Net Income Common Stockholders'))
        equity = bs.get('Stockholders Equity')
        assets = bs.get('Total Assets')
        
        fig = go.Figure()
        
        insight_text = "Données insuffisantes."
        rel_text = ""
        
        if net_income is not None and equity is not None:
            roe = (net_income / equity) * 100
            fig.add_trace(go.Scatter(x=years, y=roe, name="ROE", line=dict(color="#00C853", width=3)))
            # Analyse sur le ROE principal
            analysis = generate_financial_insight("ROE", roe)
            insight_text = analysis["insight"]
            rel_text = analysis["reliability"]
            
        if net_income is not None and assets is not None:
            roa = (net_income / assets) * 100
            fig.add_trace(go.Scatter(x=years, y=roa, name="ROA", line=dict(color="#FFD600", width=3, dash='dot')))
            
        fig.update_layout(
            title=dict(text=f"<b>RENTABILITÉ (ROE / ROA)</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=30),
            yaxis=dict(ticksuffix="%", gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
        )
        return {"fig": fig, "insight": insight_text, "reliability": rel_text}
        
    except Exception as e:
        return {"fig": go.Figure().add_annotation(text=f"Erreur: {e}", showarrow=False), "insight": "Erreur", "reliability": "0%"}

def plot_balance_sheet_structure(ticker_symbol: str) -> dict:
    """Affiche la structure du Bilan"""
    try:
        stock = yf.Ticker(ticker_symbol)
        bs = stock.balance_sheet.T.sort_index()
        
        err_result = {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}

        if bs.empty: return err_result
             
        years = bs.index.strftime('%Y')
        assets = bs.get('Total Assets')
        liabilities = bs.get('Total Liabilities Net Minority Interest', bs.get('Total Liabilities'))
        equity = bs.get('Stockholders Equity')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=assets, name='Total Assets', marker_color='#005EB8', offsetgroup=0)) # Med Blue
        fig.add_trace(go.Bar(x=years, y=liabilities, name='Liabilities', marker_color='#D93954', offsetgroup=1)) # Redish
        fig.add_trace(go.Bar(x=years, y=equity, name='Equity', marker_color='#0091DA', offsetgroup=1, base=liabilities)) # Light Blue
        
        analysis = generate_financial_insight("Assets", assets) if assets is not None else {"insight": "", "reliability": ""}
        
        fig.update_layout(
            title=dict(text=f"<b>STRUCTURE DU BILAN</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=30),
            barmode='group',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
        )
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure().add_annotation(text=f"Erreur: {e}", showarrow=False), "insight": "Erreur", "reliability": "0%"}


def plot_advanced_financials(ticker_symbol: str) -> list:
    """
    Retourne une liste de dicts : [{"fig": fig1, "insight": ...}, {"fig": fig2, ...}]
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        financials = stock.financials.T.sort_index()
        cashflow = stock.cashflow.T.sort_index()
        
        err_result = {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "N/A", "reliability": "N/A"}
        if financials.empty or cashflow.empty: return [err_result, err_result]

        years = financials.index.strftime('%Y')

        # COLORS
        color_primary = '#00338D' # KPMG Dark Blue
        color_secondary = '#0091DA' # KPMG Light Blue
        color_purple = '#48308f' # KPMG Purple
        color_text = '#cfd8dc'

        # 1. FCF
        fcf = cashflow.get('Free Cash Flow')
        if fcf is None:
            op_cf = cashflow.get('Total Cash From Operating Activities', cashflow.get('Operating Cash Flow'))
            capex = cashflow.get('Capital Expenditures')
            fcf = (op_cf + capex) if (op_cf is not None and capex is not None) else pd.Series([0]*len(years), index=years)

        fig_fcf = go.Figure(go.Bar(
            x=years, 
            y=fcf, 
            name='FCF', 
            marker_color=color_secondary,
            text=fcf,
            textposition='auto',
            texttemplate='%{text:.2s}'
        ))
        fig_fcf.update_layout(
            title=dict(text="<b>FREE CASH FLOW</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
            margin=dict(l=40, r=20, t=60, b=30)
        )
        
        fcf_analysis = generate_financial_insight("FCF", fcf)
        
        # 2. Marges
        revenue = financials.get('Total Revenue', financials.get('Revenue'))
        net_income = financials.get('Net Income', financials.get('Net Income Common Stockholders'))
        
        fig_margins = go.Figure()
        margin_analysis = {"insight": "Données incomplètes", "reliability": ""}
        
        if revenue is not None and net_income is not None:
            net_margin = (net_income / revenue) * 100
            fig_margins.add_trace(go.Scatter(
                x=years, 
                y=net_margin, 
                mode='lines+markers', 
                name='Marge Nette', 
                line=dict(color=color_purple, width=4),
                marker=dict(size=8, color='white', line=dict(width=2, color=color_purple))
            ))
            margin_analysis = generate_financial_insight("Marge Nette", net_margin)
            
        fig_margins.update_layout(
            title=dict(text="<b>EVOLUTION DES MARGES NETTES (%)</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
            margin=dict(l=40, r=20, t=60, b=30)
        )

        return [
            {"fig": fig_fcf, "insight": fcf_analysis["insight"], "reliability": fcf_analysis["reliability"]},
            {"fig": fig_margins, "insight": margin_analysis["insight"], "reliability": margin_analysis["reliability"]}
        ]

    except Exception as e:
        return [err_result, err_result]


def plot_stock_history(ticker_symbol: str, period: str = "1y") -> dict:
    """Graphique Historique avec style KPMG Pro"""
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period)
        
        if hist.empty: return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        # KPMG Colors
        color_increase = '#0091DA' # Light Blue
        color_decrease = '#6D2077' # Purple (Secondary) -> or Red equivalent for readability, let's Stick to standard Green/Red for Candles but stylized
        # Actually standard for candles is nicer for traders, let's keep green/red but polished
        
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, 
            open=hist['Open'], 
            high=hist['High'], 
            low=hist['Low'], 
            close=hist['Close'], 
            name=ticker_symbol,
            increasing_line_color='#00C853', # Material Green
            decreasing_line_color='#FF3D00'  # Material Red
        )])
        
        fig.update_layout(
            title=dict(
                text=f"COURS DE BOURSE : <b>{ticker_symbol}</b>",
                font=dict(family="Arial", size=18, color="#00338D") # KPMG Blue Title
            ),
            template="plotly_white", # Cleaner base
            paper_bgcolor="rgba(0,0,0,0)", # Transparent for integration
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=30),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            font=dict(family="Arial, sans-serif", color="#cfd8dc")
        )
        
        # Insight
        analysis = generate_financial_insight("Cours", hist['Close'])
        
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


def plot_financial_kpis(ticker_symbol: str) -> dict:
    """KPIs Revenues vs Profit"""
    try:
        stock = yf.Ticker(ticker_symbol)
        financials = stock.financials.T.sort_index()
        
        if financials.empty: return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        years = financials.index.strftime('%Y')
        revenue = financials.get('Total Revenue', financials.get('Revenue'))
        net_income = financials.get('Net Income', financials.get('Net Income Common Stockholders'))
        
        if revenue is None: return {"fig": go.Figure(), "insight": "Pas de données revenus", "reliability": ""}
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=revenue, name='CA', marker_color='#00338D')) # KPMG Blue
        if net_income is not None: fig.add_trace(go.Bar(x=years, y=net_income, name='Net', marker_color='#0091DA')) # KPMG Light Blue
        
        fig.update_layout(
            title=dict(text=f"<b>REVENUS vs RESULTAT NET</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=30),
            barmode='group',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
        )
        
        analysis = generate_financial_insight("Revenus", revenue)
        
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}

# ═══════════════════════════════════════════════════════════════
# SECTION 2 : VISUALISATIONS STRATÉGIQUES (IA)
# ═══════════════════════════════════════════════════════════════

def get_llm():
    """Initialise le LLM Mistral"""
    return ChatMistralAI(
        model="mistral-small",
        temperature=0.2,
        mistral_api_key=os.getenv("MISTRAL_API_KEY")
    )

def generate_swot_data(company: str):
    """Génère les données SWOT structurées via LLM"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Tu es un analyste stratégique expert. Analyse l'entreprise {company}.
    Génère une analyse SWOT (Strengths, Weaknesses, Opportunities, Threats) concise.
    
    FORMAT DE SORTIE ATTENDU (JSON UNIQUEMENT) :
    {{
        "strengths": ["point 1", "point 2", "point 3"],
        "weaknesses": ["point 1", "point 2", "point 3"],
        "opportunities": ["point 1", "point 2", "point 3"],
        "threats": ["point 1", "point 2", "point 3"]
    }}
    
    Ne mets rien d'autre que du JSON. Max 3-4 points par catégorie. Soyez précis et factuel.
    """)
    
    chain = prompt | llm
    response = chain.invoke({"company": company})
    
    try:
        # Nettoyage basique pour s'assurer que c'est du JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        if content.startswith("```"):
            content = content.replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Erreur parsing JSON SWOT : {e}")
        return None

def generate_swot_matrix(company: str) -> go.Figure:
    """Crée une matrice SWOT visuelle avec Plotly"""
    data = generate_swot_data(company)
    
    if not data:
        return go.Figure().add_annotation(text="Erreur lors de la génération du SWOT", showarrow=False, font=dict(color="white"))

    fig = go.Figure()

    # Définition des quadrants
    quadrants = [
        {"x": 0.5, "y": 1.5, "title": "STRENGTHS (Forces)", "color": "#4caf50", "items": data.get("strengths", [])},
        {"x": 1.5, "y": 1.5, "title": "WEAKNESSES (Faiblesses)", "color": "#f44336", "items": data.get("weaknesses", [])},
        {"x": 0.5, "y": 0.5, "title": "OPPORTUNITIES (Opportunités)", "color": "#2196f3", "items": data.get("opportunities", [])},
        {"x": 1.5, "y": 0.5, "title": "THREATS (Menaces)", "color": "#ff9800", "items": data.get("threats", [])}
    ]

    for q in quadrants:
        title_y = 1.9 if q["y"] > 1 else 0.9
        title_x = 0.5 if q["x"] < 1 else 1.5
        
        # Titre du quadrant
        fig.add_annotation(
            x=title_x, y=title_y,
            text=f"<b>{q['title']}</b>",
            showarrow=False,
            font=dict(size=12, color="white"), 
            bgcolor=q["color"], 
            opacity=0.9
        )
        
        # Layout parametres
        MAX_ITEMS = 4
        MAX_CHARS = 45
        START_Y = q["y"] - 0.2
        LINE_HEIGHT = 0.15
        
        items_data = q["items"][:MAX_ITEMS]
        
        # Préparation des données pour Scatter (Hover) + Annotation (Texte affiché)
        hover_texts = []
        display_texts = []
        y_positions = []
        x_positions = []
        
        for i, item_obj in enumerate(items_data):
            # 1. Gestion des formats (dict vs string)
            if isinstance(item_obj, dict):
                text_content = item_obj.get("item", "")
                evidence = item_obj.get("evidence", "N/A")
            else:
                text_content = str(item_obj)
                evidence = "Pas de preuve spécifiée"
            
            # 2. Construction du Hover Text (Riche HTML)
            hover_html = (
                f"<b>{text_content}</b><br><br>"
                f"🔎 <i>Preuve: {evidence}</i>"
            )
            hover_texts.append(hover_html)
            
            # 3. Construction du Texte Affiché (Tronqué)
            if len(text_content) > MAX_CHARS:
                display_text = text_content[:MAX_CHARS-3] + "..."
            else:
                display_text = text_content
            display_texts.append(f"• {display_text}")
            
            # 4. Positions
            y_positions.append(START_Y - (i * LINE_HEIGHT))
            # Position X centrée relative au quadrant
            x_pos = 0.5 if q["x"] < 1 else 1.5
            x_positions.append(x_pos)

        # Si trop d'items, on ajoute une ligne indicative (pas de hover)
        if len(q["items"]) > MAX_ITEMS:
            y_positions.append(START_Y - (MAX_ITEMS * LINE_HEIGHT))
            x_positions.append(0.5 if q["x"] < 1 else 1.5)
            display_texts.append(f"<i>(+{len(q['items']) - MAX_ITEMS} autres)</i>")
            hover_texts.append("") # Pas de hover

        # AJOUT TRACE SCATTER (Invisible markers pour le hover)
        # On utilise mode="text" pour afficher le texte tronqué directement
        # Et hovertext pour l'infobulle complète
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=y_positions,
            text=display_texts,      # Ce qui est affiché sur le graphe
            hovertext=hover_texts,   # Ce qui est affiché au survol
            mode="text",
            textfont=dict(size=10, color="#e0e0e0"),
            hoverinfo="text",
            showlegend=False,
            textposition="middle center" 
        ))

    # Zones de couleurs distinctes (Heatmap style)
    shapes = []
    shapes.append(dict(type="rect", x0=0, y0=1, x1=1, y1=2, fillcolor="rgba(76, 175, 80, 0.05)", line=dict(color="#4caf50", width=1)))
    shapes.append(dict(type="rect", x0=1, y0=1, x1=2, y1=2, fillcolor="rgba(244, 67, 54, 0.05)", line=dict(color="#f44336", width=1)))
    shapes.append(dict(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="rgba(33, 150, 243, 0.05)", line=dict(color="#2196f3", width=1)))
    shapes.append(dict(type="rect", x0=1, y0=0, x1=2, y1=1, fillcolor="rgba(255, 152, 0, 0.05)", line=dict(color="#ff9800", width=1)))

    fig.update_layout(
        title=dict(text=f"<b>MATRICE SWOT : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        xaxis=dict(range=[0, 2], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[0, 2], showgrid=False, zeroline=False, visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=650,
        shapes=shapes,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def generate_bcg_data(company: str):
    """Estime les segments pour la matrice BCG via LLM"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Identify the 4-5 main business units/products of {company}.
    For each, estimate relative Market Share (0.0 to 1.0) and Market Growth Rate (0.0 to 1.0).
    Market Share > 0.5 is High. Growth > 0.5 is High.
    
    OUTPUT FORMAT (JSON ONLY):
    [
        {{"name": "Product A", "market_share": 0.8, "growth": 0.2, "revenue_weight": 50}},
        {{"name": "Product B", "market_share": 0.3, "growth": 0.8, "revenue_weight": 30}}
    ]
    Revenue weight is mostly for bubble size (approximate).
    """)
    
    chain = prompt | llm
    response = chain.invoke({"company": company})
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Erreur parsing JSON BCG : {e}")
        return []

def generate_bcg_matrix(company: str) -> go.Figure:
    """Crée une matrice BCG (Boston Consulting Group)"""
    products = generate_bcg_data(company)
    
    if not products:
        return go.Figure().add_annotation(text="Erreur génération BCG", showarrow=False, font=dict(color="white"))
        
    df = pd.DataFrame(products)
    
    fig = px.scatter(
        df,
        x="market_share",
        y="growth",
        size="revenue_weight",
        color="name",
        text="name",
        title=f"Matrice BCG : {company}",
        labels={"market_share": "Part de Marché Relative (Cash Generation)", "growth": "Taux de Croissance (Cash Usage)"},
        template="plotly_dark"
    )
    
    fig.update_xaxes(autorange="reversed", gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc'))
    fig.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="gray")
    fig.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="gray")
    
    # Annotations des quadrants
    fig.add_annotation(x=0.8, y=0.9, text="STARS", showarrow=False, font=dict(color="#FFD600"))
    fig.add_annotation(x=0.2, y=0.9, text="QUESTION MARKS", showarrow=False, font=dict(color="#00E5FF"))
    fig.add_annotation(x=0.8, y=0.1, text="CASH COWS", showarrow=False, font=dict(color="#00C853"))
    fig.add_annotation(x=0.2, y=0.1, text="DOGS", showarrow=False, font=dict(color="#FF3D00"))

    fig.update_xaxes(range=[1.0, 0.0]) 
    fig.update_yaxes(range=[0.0, 1.0])
    
    fig.update_traces(textposition='top center')
    fig.update_layout(
        title=dict(text=f"<b>MATRICE BCG : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600, 
        showlegend=False,
        font=dict(family="Arial, sans-serif", color="#cfd8dc")
    )
    
    return fig

def generate_pestel_data(company: str):
    """Génère une analyse PESTEL structurée via LLM (Score 0-10 + Détails)"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Tu es un expert en stratégie d'entreprise. Réalise une analyse PESTEL pour {company}.
    Pour chaque dimension, donne un score d'impact/risque (0 = Faible impact/Risque, 10 = Fort impact/Critique) et une courte explication.

    FORMAT DE SORTIE ATTENDU (JSON UNIQUEMENT) :
    {{
        "Politique": {{"score": 7, "details": "Conflits commerciaux..."}},
        "Economique": {{"score": 5, "details": "Inflation..."}},
        "Societal": {{"score": 3, "details": "Changement habitudes..."}},
        "Technologique": {{"score": 9, "details": "IA générative..."}},
        "Environnemental": {{"score": 8, "details": "Objectifs carbone..."}},
        "Legal": {{"score": 6, "details": "Régulations UE..."}}
    }}
    """)
    
    chain = prompt | llm
    response = chain.invoke({"company": company})
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Erreur parsing JSON PESTEL : {e}")
        return None

def generate_pestel_radar(company: str) -> go.Figure:
    """Crée un Radar Chart pour l'analyse PESTEL"""
    data = generate_pestel_data(company)
    
    if not data:
        return go.Figure().add_annotation(text="Erreur génération PESTEL", showarrow=False, font=dict(color="white"))

    categories = list(data.keys())
    scores = [v["score"] for v in data.values()]
    details = [v["details"] for v in data.values()] 

    categories.append(categories[0])
    scores.append(scores[0])
    details.append(details[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 51, 141, 0.4)', # Bleu KPMG transparent
        line=dict(color='#00338D', width=3),
        name=company,
        hovertext=details,
        hoverinfo="text+r"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=True,
                tickfont=dict(color="#cfd8dc"),
                linecolor="gray",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            angularaxis=dict(
                tickfont=dict(color="#00338D", size=14, weight="bold"), # KPMG Blue Titles for PESTEL axes
                linecolor="gray",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        title=dict(text=f"<b>ANALYSE PESTEL : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
        showlegend=False
    )

    return fig

# ═══════════════════════════════════════════════════════════════
# SECTION 3 : VISUALISATIONS BASÉES SUR FACTS (Centralisées)
# ═══════════════════════════════════════════════════════════════

def _get_source_annotation(facts: dict) -> dict:
    """Helper pour générer l'annotation de source standard."""
    info = facts.get("info", {})
    exchange = info.get("exchange", "N/A")
    currency = info.get("currency", "USD")
    retrieved = facts.get("retrieved_at", datetime.now().isoformat())[:10] # Date YYYY-MM-DD
    
    return dict(
        text=f" Source: Yahoo Finance ({exchange}: {currency}) • Mis à jour: {retrieved}",
        xref="paper", yref="paper",
        x=0, y=-1,  # Coin bas droite, DANS la zone visible
        showarrow=False,
        font=dict(size=9, color="#90a4ae"),
        xanchor="right", yanchor="bottom"
    )

def plot_stock_history_from_facts(facts: dict, ticker_symbol: str) -> dict:
    """Génère le graphique de cours à partir des données FACTS pré-chargées."""
    try:
        hist = facts.get("history")
        
        if hist is None or hist.empty:
            return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, 
            open=hist['Open'], 
            high=hist['High'], 
            low=hist['Low'], 
            close=hist['Close'], 
            name=ticker_symbol,
            increasing_line_color='#00C853',
            decreasing_line_color='#FF3D00'
        )])
        
        fig.update_layout(
            title=dict(text=f"COURS DE BOURSE : <b>{ticker_symbol}</b>", font=dict(family="Arial", size=18, color="#FFFFFF")),
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=50), # Augmenter marge bas pour source
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            font=dict(family="Arial, sans-serif", color="#cfd8dc"),
            annotations=[_get_source_annotation(facts)]
        )
        
        analysis = generate_financial_insight("Cours", hist['Close'])
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


def plot_financial_kpis_from_facts(facts: dict) -> dict:
    """Génère le graphique Revenus vs Net à partir des données FACTS."""
    try:
        derived = facts.get("derived", {})
        revenue = derived.get("revenue")
        net_income = derived.get("net_income")
        
        if revenue is None:
            return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        years = revenue.index.strftime('%Y')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=revenue, name='CA', marker_color='#00338D'))
        if net_income is not None:
            fig.add_trace(go.Bar(x=years, y=net_income, name='Net', marker_color='#0091DA'))
        
        fig.update_layout(
            title=dict(text="<b>REVENUS vs RESULTAT NET</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=60, b=50),
            barmode='group',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            annotations=[_get_source_annotation(facts)]
        )
        
        analysis = generate_financial_insight("Revenus", revenue)
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


def plot_advanced_financials_from_facts(facts: dict) -> list:
    """Génère FCF et Marges à partir des données FACTS."""
    try:
        derived = facts.get("derived", {})
        color_primary = '#00338D'
        color_secondary = '#0091DA'
        color_purple = '#48308f'
        color_text = '#cfd8dc'
        
        err_result = {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "N/A", "reliability": "N/A"}
        
        # FCF
        fcf = derived.get("fcf")
        if fcf is not None and not fcf.empty:
            years = fcf.index.strftime('%Y')
            fig_fcf = go.Figure(go.Bar(x=years, y=fcf, name='FCF', marker_color=color_secondary, text=fcf, textposition='auto', texttemplate='%{text:.2s}'))
            fig_fcf.update_layout(
                title=dict(text="<b>FREE CASH FLOW</b>", font=dict(color=color_primary, size=18)),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
                margin=dict(l=40, r=20, t=60, b=50),
                annotations=[_get_source_annotation(facts)]
            )
            fcf_analysis = generate_financial_insight("FCF", fcf)
            fcf_result = {"fig": fig_fcf, "insight": fcf_analysis["insight"], "reliability": fcf_analysis["reliability"]}
        else:
            fcf_result = err_result
        
        # Marges
        net_margin = derived.get("net_margin")
        if net_margin is not None and not net_margin.empty:
            years = net_margin.index.strftime('%Y')
            fig_margins = go.Figure()
            fig_margins.add_trace(go.Scatter(x=years, y=net_margin, mode='lines+markers', name='Marge Nette', 
                                              line=dict(color=color_purple, width=4),
                                              marker=dict(size=8, color='white', line=dict(width=2, color=color_purple))))
            fig_margins.update_layout(
                title=dict(text="<b>EVOLUTION DES MARGES NETTES (%)</b>", font=dict(color=color_primary, size=18)),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color=color_text)),
                margin=dict(l=40, r=20, t=60, b=50),
                annotations=[_get_source_annotation(facts)]
            )
            margin_analysis = generate_financial_insight("Marge Nette", net_margin)
            margin_result = {"fig": fig_margins, "insight": margin_analysis["insight"], "reliability": margin_analysis["reliability"]}
        else:
            margin_result = err_result
        
        return [fcf_result, margin_result]
        
    except Exception as e:
        err = {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}
        return [err, err]


def plot_solvency_from_facts(facts: dict) -> dict:
    """Génère le graphique de solvabilité à partir des données FACTS."""
    try:
        derived = facts.get("derived", {})
        de_ratio = derived.get("debt_to_equity")
        
        if de_ratio is None or de_ratio.empty:
            return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        years = de_ratio.index.strftime('%Y')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=de_ratio, name='Debt to Equity Ratio', marker_color='#F68D2E'))
        
        fig.update_layout(
            title=dict(text="<b>SOLVABILITÉ (Debt/Equity)</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
            margin=dict(l=40, r=20, t=60, b=50),
            shapes=[dict(type="line", x0=years[0], y0=2.0, x1=years[-1], y1=2.0, line=dict(color="#FF3D00", width=2, dash="dash"))],
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            annotations=[_get_source_annotation(facts)]
        )
        
        analysis = generate_financial_insight("Ratio Dette/Equity", de_ratio)
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


def plot_returns_from_facts(facts: dict) -> dict:
    """Génère ROE/ROA à partir des données FACTS."""
    try:
        derived = facts.get("derived", {})
        roe = derived.get("roe")
        roa = derived.get("roa")
        
        if roe is None and roa is None:
            return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        fig = go.Figure()
        insight_text = "Données insuffisantes."
        rel_text = ""
        
        if roe is not None and not roe.empty:
            years = roe.index.strftime('%Y')
            fig.add_trace(go.Scatter(x=years, y=roe, name="ROE", line=dict(color="#00C853", width=3)))
            analysis = generate_financial_insight("ROE", roe)
            insight_text = analysis["insight"]
            rel_text = analysis["reliability"]
            
        if roa is not None and not roa.empty:
            years = roa.index.strftime('%Y')
            fig.add_trace(go.Scatter(x=years, y=roa, name="ROA", line=dict(color="#FFD600", width=3, dash='dot')))
        
        fig.update_layout(
            title=dict(text="<b>RENTABILITÉ (ROE / ROA)</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
            margin=dict(l=40, r=20, t=60, b=50),
            yaxis=dict(ticksuffix="%", gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            annotations=[_get_source_annotation(facts)]
        )
        
        return {"fig": fig, "insight": insight_text, "reliability": rel_text}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


def plot_balance_sheet_from_facts(facts: dict) -> dict:
    """Génère la structure du bilan à partir des données FACTS."""
    try:
        derived = facts.get("derived", {})
        assets = derived.get("total_assets")
        liabilities = derived.get("total_liabilities")
        equity = derived.get("stockholders_equity")
        
        if assets is None:
            return {"fig": go.Figure().add_annotation(text="Pas de données", showarrow=False, font=dict(color="white")), "insight": "", "reliability": ""}
        
        years = assets.index.strftime('%Y')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=assets, name='Total Assets', marker_color='#005EB8', offsetgroup=0))
        if liabilities is not None:
            fig.add_trace(go.Bar(x=years, y=liabilities, name='Liabilities', marker_color='#D93954', offsetgroup=1))
        if equity is not None:
            fig.add_trace(go.Bar(x=years, y=equity, name='Equity', marker_color='#0091DA', offsetgroup=1, base=liabilities))
        
        fig.update_layout(
            title=dict(text="<b>STRUCTURE DU BILAN</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
            margin=dict(l=40, r=20, t=60, b=50), barmode='group',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            annotations=[_get_source_annotation(facts)]
        )
        
        analysis = generate_financial_insight("Assets", assets)
        return {"fig": fig, "insight": analysis["insight"], "reliability": analysis["reliability"]}
        
    except Exception as e:
        return {"fig": go.Figure(), "insight": f"Erreur: {e}", "reliability": "0%"}


# ═══════════════════════════════════════════════════════════════
# SECTION 4 : VISUALISATIONS STRATÉGIQUES FROM FACTS (Centralisées)
# ═══════════════════════════════════════════════════════════════

def generate_swot_from_strategic_facts(strategic_data: dict, company: str) -> go.Figure:
    """
    Crée une matrice SWOT visuelle à partir des données Strategic FACTS pré-générées.
    
    Args:
        strategic_data: Données du strategic_facts_service
        company: Nom de l'entreprise pour le titre
    
    Returns:
        go.Figure: Matrice SWOT Plotly
    """
    swot = strategic_data.get("swot", {})
    
    if not swot or strategic_data.get("error"):
        return go.Figure().add_annotation(
            text=f"Erreur: {strategic_data.get('error', 'Données SWOT manquantes')}", 
            showarrow=False, 
            font=dict(color="white")
        )

    fig = go.Figure()

    # Définition des quadrants avec positions ajustées pour remplir les cases
    # Chaque quadrant occupe une zone de 1x1 dans un espace 2x2
    quadrants = [
        {
            "title": "STRENGTHS", 
            "color": "#4caf50", 
            "items": swot.get("strengths", []),
            "x_range": (0.05, 0.95),   # Zone X du quadrant (gauche)
            "y_range": (1.05, 1.85),   # Zone Y du quadrant (haut)
            "title_pos": (0.5, 1.92)
        },
        {
            "title": "WEAKNESSES", 
            "color": "#f44336", 
            "items": swot.get("weaknesses", []),
            "x_range": (1.05, 1.95),   # Zone X du quadrant (droite)
            "y_range": (1.05, 1.85),   # Zone Y du quadrant (haut)
            "title_pos": (1.5, 1.92)
        },
        {
            "title": "OPPORTUNITIES", 
            "color": "#2196f3", 
            "items": swot.get("opportunities", []),
            "x_range": (0.05, 0.95),   # Zone X du quadrant (gauche)
            "y_range": (0.15, 0.90),   # Zone Y du quadrant (bas)
            "title_pos": (0.5, 0.95)
        },
        {
            "title": "THREATS", 
            "color": "#ff9800", 
            "items": swot.get("threats", []),
            "x_range": (1.05, 1.95),   # Zone X du quadrant (droite)
            "y_range": (0.15, 0.90),   # Zone Y du quadrant (bas)
            "title_pos": (1.5, 0.95)
        }
    ]

    for q in quadrants:
        # Titre du quadrant
        fig.add_annotation(
            x=q["title_pos"][0], y=q["title_pos"][1],
            text=f"<b>{q['title']}</b>",
            showarrow=False,
            font=dict(size=13, color="white"), 
            bgcolor=q["color"], 
            borderpad=4,
            opacity=0.95
        )
        
        # Paramètres de layout
        MAX_ITEMS = 5
        MAX_CHARS = 40
        
        items_data = q["items"][:MAX_ITEMS]
        n_items = len(items_data)
        
        if n_items == 0:
            continue
        
        # Calcul des positions Y uniformément réparties dans le quadrant
        y_min, y_max = q["y_range"]
        y_span = y_max - y_min
        item_spacing = y_span / (n_items + 1)
        
        # Position X centrée dans le quadrant
        x_center = (q["x_range"][0] + q["x_range"][1]) / 2
        
        hover_texts = []
        display_texts = []
        y_positions = []
        x_positions = []
        text_colors = []
        
        for i, item_obj in enumerate(items_data):
            # Gestion des formats (dict vs string)
            if isinstance(item_obj, dict):
                text_content = item_obj.get("item", "")
                evidence = item_obj.get("evidence", "N/A")
                is_financial = item_obj.get("source") == "financial"
                # Source citée (LLM ou Yahoo Finance)
                source_citation = item_obj.get("source", "Non spécifiée")
                source_type = item_obj.get("source_type", "")
            else:
                text_content = str(item_obj)
                evidence = "Pas de preuve spécifiée"
                is_financial = False
                source_citation = "Non spécifiée"
                source_type = ""
            
            # Icône pour différencier les sources
            icon = "" if is_financial else ""
            
            # Label de source pour le hover
            if is_financial:
                source_display = "Yahoo Finance (données temps réel)"
                source_type_display = "📈 Donnée Financière"
            else:
                source_display = source_citation if source_citation != "financial" else "Non spécifiée"
                type_icons = {
                    "rapport_financier": "",
                    "presse": "",
                    "analyse_marche": "",
                    "regulateur": ""
                }
                source_type_display = f"{type_icons.get(source_type, '')} {source_type.replace('_', ' ').title()}" if source_type else "Analyse IA"
            
            category_label = q["title"]
            
            # Source abrégée pour affichage direct
            if is_financial:
                source_short = " Yahoo Finance"
            else:
                # Tronquer la source si trop longue
                if len(source_citation) > 25:
                    source_short = f"{source_citation[:22]}..."
                else:
                    source_short = f"{source_citation}"
            
            # Construction du Texte Affiché (contenu + source sur une ligne)
            if len(text_content) > 30:
                display_text = text_content[:27] + "..."
            else:
                display_text = text_content
            
            # Format: icône + contenu (source)
            if len(source_short) > 20:
                source_display = source_short[:17] + "..."
            else:
                source_display = source_short
            
            # Utilisation de <br> pour le saut de ligne + span pour le style (taille/couleur)
            # Plotly supporte un sous-ensemble HTML
            full_display = f"{icon} {display_text}<br><span style='font-size:10px;color:#90a4ae'>{source_display}</span>"
            display_texts.append(full_display)
            
            # Position Y: répartie uniformément du haut vers le bas du quadrant
            y_pos = y_max - (i + 1) * item_spacing
            y_positions.append(y_pos)
            x_positions.append(x_center)
            
            # Couleur différente pour les items financiers
            text_colors.append("#90caf9" if is_financial else "#e0e0e0")

        # AJOUT TRACE SCATTER pour ce quadrant
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=y_positions,
            text=display_texts,
            mode="text",
            textfont=dict(size=9, color=text_colors),
            showlegend=False,
            textposition="middle center",
            cliponaxis=False
        ))

    # Zones de couleurs distinctes (rectangles de fond)
    shapes = [
        dict(type="rect", x0=0, y0=1, x1=1, y1=2, fillcolor="rgba(76, 175, 80, 0.08)", line=dict(color="#4caf50", width=2)),
        dict(type="rect", x0=1, y0=1, x1=2, y1=2, fillcolor="rgba(244, 67, 54, 0.08)", line=dict(color="#f44336", width=2)),
        dict(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="rgba(33, 150, 243, 0.08)", line=dict(color="#2196f3", width=2)),
        dict(type="rect", x0=1, y0=0, x1=2, y1=1, fillcolor="rgba(255, 152, 0, 0.08)", line=dict(color="#ff9800", width=2))
    ]

    # Annotation source
    source_text = f"Financier + 💡 IA | {strategic_data.get('ticker', 'N/A')} | {strategic_data.get('generated_at', '')[:10]}"
    
    fig.update_layout(
        title=dict(text=f"<b>MATRICE SWOT : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        xaxis=dict(range=[0, 2], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        yaxis=dict(range=[0, 2], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600,
        shapes=shapes,
        margin=dict(l=10, r=10, t=50, b=40),
        annotations=[
            dict(
                text=source_text,
                xref="paper", yref="paper",
                x=0.5, y=-0.05,
                showarrow=False,
                font=dict(size=10, color="#90a4ae"),
                xanchor="center"
            )
        ]
    )
    
    return fig


def generate_bcg_from_strategic_facts(strategic_data: dict, company: str) -> go.Figure:
    """
    Crée une matrice BCG à partir des données Strategic FACTS pré-générées.
    
    Args:
        strategic_data: Données du strategic_facts_service
        company: Nom de l'entreprise pour le titre
    
    Returns:
        go.Figure: Matrice BCG Plotly
    """
    products = strategic_data.get("bcg", [])
    
    if not products or strategic_data.get("error"):
        return go.Figure().add_annotation(
            text=f"Erreur: {strategic_data.get('error', 'Données BCG manquantes')}", 
            showarrow=False, 
            font=dict(color="white")
        )
    
    # Créer les hover texts avec sources
    hover_texts = []
    display_texts = []
    for p in products:
        name = p.get("name", "N/A")
        ms = p.get("market_share", 0)
        growth = p.get("growth", 0)
        source = p.get("source", "Source non détectée")
        
        # Déterminer le quadrant
        if ms > 0.5 and growth > 0.5:
            quadrant = "⭐ STAR"
        elif ms <= 0.5 and growth > 0.5:
            quadrant = "❓ QUESTION MARK"
        elif ms > 0.5 and growth <= 0.5:
            quadrant = "🐄 CASH COW"
        else:
            quadrant = "🐕 DOG"
        
        hover = (
            f"<b style='font-size:14px'>{name}</b><br>"
            f"<span style='color:#90a4ae'>━━━━━━━━━━━━━━━━━━━━━</span><br><br>"
            f"<b>Part de marché:</b> {ms*100:.0f}%<br>"
            f"<b>Croissance:</b> {growth*100:.0f}%<br>"
            f"<b>Position:</b> {quadrant}<br><br>"
            f"<b>Source:</b> {source}<br>"
            f"<span style='color:#78909c; font-size:11px'>Entreprise: {company}</span>"
        )
        # Tronquer la source
        if len(source) > 20:
            source_short = source[:17] + "..."
        else:
            source_short = source
        
        # Texte affiché: nom + source sur 2 lignes (avec \n)
        display_text = f"{name}\n📰 {source_short}"
        display_texts.append(display_text)
    
    df = pd.DataFrame(products)
    df["display_text"] = display_texts
    
    fig = go.Figure()
    
    # Créer le scatter plot avec source affichée directement
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["market_share"]],
            y=[row["growth"]],
            mode="markers+text",
            marker=dict(size=row.get("revenue_weight", 30), opacity=0.7),
            text=[row["display_text"]],
            textposition="top center",
            showlegend=False,
            textfont=dict(color="#e0e0e0", size=10)
        ))
    
    fig.update_xaxes(
        autorange="reversed", 
        range=[1.0, 0.0],
        gridcolor='rgba(255,255,255,0.1)', 
        tickfont=dict(color='#cfd8dc'),
        title="Part de Marché Relative"
    )
    fig.update_yaxes(
        range=[0.0, 1.0],
        gridcolor='rgba(255,255,255,0.1)', 
        tickfont=dict(color='#cfd8dc'),
        title="Taux de Croissance"
    )
    fig.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="gray")
    fig.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="gray")
    
    # Annotation source globale
    source_text = f"IA: Mistral | Financier: {strategic_data.get('ticker', 'N/A')} | {strategic_data.get('generated_at', '')[:10]}"
    
    fig.update_layout(
        title=dict(text=f"<b>MATRICE BCG : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600, 
        showlegend=False,
        font=dict(family="Arial, sans-serif", color="#cfd8dc"),
        margin=dict(l=60, r=20, t=60, b=60),
        annotations=[
            dict(x=0.8, y=0.9, text="⭐ STARS", showarrow=False, font=dict(color="#FFD600", size=12)),
            dict(x=0.2, y=0.9, text="❓ QUESTION MARKS", showarrow=False, font=dict(color="#00E5FF", size=12)),
            dict(x=0.8, y=0.1, text="🐄 CASH COWS", showarrow=False, font=dict(color="#00C853", size=12)),
            dict(x=0.2, y=0.1, text="🐕 DOGS", showarrow=False, font=dict(color="#FF3D00", size=12)),
            dict(
                text=source_text,
                xref="paper", yref="paper",
                x=0.5, y=-0.12,
                showarrow=False,
                font=dict(size=10, color="#90a4ae"),
                xanchor="center"
            )
        ]
    )
    
    return fig


def generate_pestel_from_strategic_facts(strategic_data: dict, company: str) -> go.Figure:
    """
    Crée un Radar Chart PESTEL à partir des données Strategic FACTS pré-générées.
    
    Args:
        strategic_data: Données du strategic_facts_service
        company: Nom de l'entreprise pour le titre
    
    Returns:
        go.Figure: Radar PESTEL Plotly
    """
    pestel = strategic_data.get("pestel", {})
    
    if not pestel or strategic_data.get("error"):
        return go.Figure().add_annotation(
            text=f"Erreur: {strategic_data.get('error', 'Données PESTEL manquantes')}", 
            showarrow=False, 
            font=dict(color="white")
        )

    categories = list(pestel.keys())
    scores = [v.get("score", 0) if isinstance(v, dict) else 0 for v in pestel.values()]
    details = [v.get("details", "") if isinstance(v, dict) else "" for v in pestel.values()]
    sources = [v.get("source", "Source non détectée") if isinstance(v, dict) else "Source non détectée" for v in pestel.values()]
    
    # Construire les labels avec sources
    labels_with_sources = []
    source_annotations = []
    
    # Positions angulaires pour les annotations (en degrés, 6 dimensions)
    angles = [90, 30, -30, -90, -150, 150]  # Positions pour P, E, S, T, E, L
    
    for i, (cat, score, detail, source) in enumerate(zip(categories, scores, details, sources)):
        # Icône par dimension
        cat_icons = {
            "Politique": "",
            "Economique": "",
            "Societal": "",
            "Technologique": "",
            "Environnemental": "",
            "Legal": ""
        }
        icon = cat_icons.get(cat, "")
        
        # Niveau de risque
        if score >= 8:
            risk_badge = "🔴"
        elif score >= 6:
            risk_badge = "🟠"
        elif score >= 4:
            risk_badge = "🟡"
        else:
            risk_badge = "🟢"
        
        # Label enrichi : catégorie + score + risque
        label = f"{icon} {cat} ({score}/10) {risk_badge}"
        labels_with_sources.append(label)
        
        # Tronquer la source
        if len(source) > 20:
            source_short = source[:17] + "..."
        else:
            source_short = source

    # Fermer le radar
    categories_closed = labels_with_sources + [labels_with_sources[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(0, 51, 141, 0.4)',
        line=dict(color='#CCCCFF', width=3),
        name=company
    ))

    # Créer une légende des sources en bas
    sources_legend = "<br>".join([f"{cat_icons.get(cat, '')} {cat}: 📰 {src}" for cat, src in zip(categories, sources)])
    
    # Annotation source globale
    source_text = f"IA: Mistral | Financier: {strategic_data.get('ticker', 'N/A')} | {strategic_data.get('generated_at', '')[:10]}"

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=True,
                tickfont=dict(color="#cfd8dc"),
                linecolor="gray",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            angularaxis=dict(
                tickfont=dict(color="#FFFFFF", size=11, weight="bold"),
                linecolor="gray",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        title=dict(text=f"<b>ANALYSE PESTEL : {company}</b>", font=dict(color="#FFFFFF", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550,
        showlegend=False,
        margin=dict(l=80, r=80, t=60, b=100),
        annotations=[
            dict(
                text=source_text,
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                showarrow=False,
                font=dict(size=10, color="#FFFFFF"),
                xanchor="center"
            )
        ]
    )
    
    # Ajouter une légende des sources
    sources_text = " | ".join([f"<b>{categories[i][:3]}:</b> {sources[i][:15]}..." if len(sources[i]) > 15 else f"<b>{categories[i][:3]}:</b> {sources[i]}" for i in range(len(categories))])
    fig.add_annotation(
        text=f"📰 Sources: {sources_text}",
        xref="paper", yref="paper",
        x=0.5, y=-0.22,
        showarrow=False,
        font=dict(size=9, color="#78909c"),
        xanchor="center"
    )

    return fig

# ═══════════════════════════════════════════════════════════════
# SECTION 5 : VISUALISATIONS MARKET SIZING (NOUVEAU)
# ═══════════════════════════════════════════════════════════════

def plot_market_sizing_waterfall(tam: float, sam: float, som: float, currency: str = "€") -> go.Figure:
    """
    Génère un Waterfall Chart pour TAM/SAM/SOM.
    Gère les valeurs None/0 proprement.
    """
    try:
        if tam is None: tam = 0
        if sam is None: sam = 0
        if som is None: som = 0

        # Logique Waterfall: TAM -> SAM (restriction) -> SOM (capture)
        # Mais pour un TAM/SAM/SOM classique, ce sont plutôt des barres imbriquées ou comparées.
        # Le format "Pont" (Waterfall) est souvent utilisé : 
        # TAM (Total) -> -Segments non adressés = SAM -> -Part non capturée = SOM
        
        # Calcul des deltas pour le waterfall
        delta_tam_sam = sam - tam # Négatif
        delta_sam_som = som - sam # Négatif
        
        fig = go.Figure(go.Waterfall(
            name = "Market Sizing",
            orientation = "v",
            measure = ["absolute", "relative", "relative", "total"],
            x = ["TAM (Total)", "Non Addressable", "Uncaptured", "SOM (Obtainable)"],
            textposition = "outside",
            text = [f"{tam:,.0f}{currency}", f"{delta_tam_sam:,.0f}{currency}", f"{delta_sam_som:,.0f}{currency}", f"{som:,.0f}{currency}"],
            y = [tam, delta_tam_sam, delta_sam_som, 0], # Le dernier est calculé auto par "total" mais on peut forcer 0
            connector = {"line":{"color":"#cfd8dc"}},
            decreasing = {"marker":{"color":"#ef5350"}}, # Rouge clair pour les réductions
            increasing = {"marker":{"color":"#00C853"}},
            totals = {"marker":{"color":"#00338D"}} # Bleu KPMG pour le final SOM
        ))
        
        # Alternative : Barres simples côte à côte si Waterfall trop complexe visuellement pour TAM/SAM/SOM
        # Souvent TAM SAM SOM est représenté par des cercles concentriques ou des barres dégressives à part.
        # Faisons simple : 3 Barres dégressives colorées.
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=["TAM", "SAM", "SOM"],
            y=[tam, sam, som],
            text=[f"{tam:,.0f} {currency}", f"{sam:,.0f} {currency}", f"{som:,.0f} {currency}"],
            textposition='auto',
            marker_color=['#00338D', '#005EB8', '#0091DA'] # Dégradé bleu KPMG
        ))
        
        fig_bar.update_layout(
            title=dict(text="<b>ESTIMATION TAM / SAM / SOM</b>", font=dict(color="#FFFFFF", size=18)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            xaxis=dict(tickfont=dict(color='#cfd8dc', size=14, weight="bold")),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig_bar
        
    except Exception as e:
        return go.Figure().add_annotation(text=f"Erreur Viz: {e}", showarrow=False, font=dict(color="white"))

def plot_valuation_football_field(ranges: list) -> go.Figure:
    """
    Génère un 'Football Field' chart pour comparer les méthodes de valorisation/taille.
    
    Args:
        ranges: Liste de dicts [{'label': 'Top-Down', 'min': 100, 'max': 200, 'val': 150}, ...]
    """
    try:
        fig = go.Figure()
        
        if not ranges:
            return fig.add_annotation(text="Pas de données de comparaison", showarrow=False, font=dict(color="white"))

        # Inverser pour afficher du haut vers le bas
        ranges = ranges[::-1]
        
        labels = [r['label'] for r in ranges]
        mins = [r['min'] for r in ranges]
        maxs = [r['max'] for r in ranges]
        vals = [r.get('val', (r['min']+r['max'])/2) for r in ranges]
        
        # Barre invisible pour décaler le début
        fig.add_trace(go.Bar(
            y=labels,
            x=mins,
            orientation='h',
            marker=dict(color='rgba(0,0,0,0)'),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Barre visible (Max - Min)
        rect_widths = [ma - mi for ma, mi in zip(maxs, mins)]
        
        fig.add_trace(go.Bar(
            y=labels,
            x=rect_widths,
            orientation='h',
            marker=dict(color='#0091DA', opacity=0.6, line=dict(color='#00338D', width=1)),
            base=mins, # Commence à min
            name='Plage de Valeur',
            hoverinfo='x+y'
        ))
        
        # Point central (Valeur de base)
        fig.add_trace(go.Scatter(
            y=labels,
            x=vals,
            mode='markers',
            marker=dict(color='#FFFFFF', size=10, symbol='diamond'),
            name='Cas de Base'
        ))

        fig.update_layout(
            title=dict(text="<b>TRIANGULATION DES MÉTHODES</b> (Football Field)", font=dict(color="#FFFFFF", size=18)),
            barmode='stack', # Pour que la barre commence au bon endroit
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cfd8dc')),
            yaxis=dict(tickfont=dict(color='#cfd8dc', size=12)),
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
        )
        
        return fig
        
    except Exception as e:
        return go.Figure().add_annotation(text=f"Erreur Football Field: {e}", showarrow=False, font=dict(color="white"))
