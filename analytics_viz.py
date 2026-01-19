
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
                title=dict(text=f"<b>SOLVABILITÉ (Debt/Equity)</b>", font=dict(color="#00338D", size=18)),
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
            title=dict(text=f"<b>RENTABILITÉ (ROE / ROA)</b>", font=dict(color="#00338D", size=18)),
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
            title=dict(text=f"<b>STRUCTURE DU BILAN</b>", font=dict(color="#00338D", size=18)),
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
            title=dict(text="<b>FREE CASH FLOW</b>", font=dict(color=color_primary, size=18)),
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
            title=dict(text="<b>EVOLUTION DES MARGES NETTES (%)</b>", font=dict(color=color_primary, size=18)),
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
            title=dict(text=f"<b>REVENUS vs RESULTAT NET</b>", font=dict(color="#00338D", size=18)),
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
        
        fig.add_annotation(
            x=title_x, y=title_y,
            text=f"<b>{q['title']}</b>",
            showarrow=False,
            font=dict(size=14, color="white"), 
            bgcolor=q["color"], 
            opacity=0.9
        )
        
        import textwrap
        formatted_items = []
        for item in q["items"]:
            wrapped_lines = textwrap.wrap(item, width=40) 
            formatted_item = "<br> ".join(wrapped_lines)
            formatted_items.append(f"• {formatted_item}")
            
        content_text = "<br><br>".join(formatted_items)
        x_anchor = 0.60 if q["x"] < 1 else 1.65
        
        fig.add_annotation(
            x=x_anchor, 
            y=q["y"] - 0.15,
            text=content_text,
            showarrow=False,
            font=dict(size=11, color="#e0e0e0"), # Lighter text
            align="left",
            valign="middle", 
            xref="x", 
            yref="y",
            width=380
        )

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
