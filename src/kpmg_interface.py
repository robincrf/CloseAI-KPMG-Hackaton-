
import gradio as gr
import analytics_viz
import facts_manager
import pandas as pd
from strategic_facts_service import strategic_facts_service

# Helper to format numbers
def format_currency(value):
    if value is None: return "N/A"
    if value >= 1e9: return f"€{value/1e9:.1f}B"
    if value >= 1e6: return f"€{value/1e6:.1f}M"
    if value >= 1e3: return f"€{value/1e3:.1f}K"
    return f"€{value:.0f}"

def launch_dashboard(rag_stream_function):
    """
    Lance le tableau de bord KPMG Market Sizer.
    """
    
    # Thème KPMG
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="slate",
    ).set(
        body_background_fill="#121212", 
        body_text_color="#E0E0E0",
        block_background_fill="#1E1E1E",
        block_border_width="1px",
        block_border_color="rgba(255, 255, 255, 0.1)",
        block_label_text_color="#0091DA",
        input_background_fill="#262626",
        button_primary_background_fill="#00338D",
        button_primary_text_color="white",
        button_secondary_background_fill="#262626",
        button_secondary_text_color="#0091DA",
        button_secondary_border_color="#0091DA",
        slider_color="#0091DA"
    )

    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    body, gradio-app { font-family: 'Inter', sans-serif !important; }
    .header-container {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1.5rem; background: linear-gradient(90deg, #00338D 0%, #001E55 100%);
        border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0, 51, 141, 0.3);
    }
    .header-title { color: white; font-size: 1.8rem; font-weight: 700; }
    .header-subtitle { color: #0091DA; font-size: 1rem; font-weight: 500; }
    
    /* NEW: FACTS ACCORDION STYLE */
    details.fact-details {
        background: #1E1E1E; border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px; margin-bottom: 10px; overflow: hidden;
        transition: all 0.2s ease;
    }
    details.fact-details:hover { border-color: #0091DA; }
    details.fact-details[open] { border-color: #0091DA; background: #232323; }
    
    summary.fact-summary {
        padding: 12px 15px; cursor: pointer; list-style: none;
        display: flex; align-items: center; justify-content: space-between;
        font-weight: 600; color: #E0E0E0;
    }
    summary.fact-summary::-webkit-details-marker { display: none; }
    
    .fact-value-badge {
        background: rgba(0, 145, 218, 0.2); color: #0091DA;
        padding: 4px 8px; border-radius: 4px; font-family: monospace;
    }
    
    .fact-content {
        padding: 15px; border-top: 1px solid rgba(255, 255, 255, 0.05);
        display: flex; color: #B0B0B0; font-size: 0.9rem;
    }
    .fact-explanation { flex: 2; padding-right: 20px; border-right: 1px solid rgba(255,255,255,0.1); }
    .fact-metadata { flex: 1; padding-left: 20px; display: flex; flex-direction: column; gap: 5px; }
    
    .meta-row { display: flex; justify-content: space-between; font-size: 0.8em; }
    .meta-label { opacity: 0.6; }
    .meta-val { font-weight: 600; color: white; text-align: right; }
    """

    with gr.Blocks(title="KPMG Market Sizer") as demo:
        
        # HEADER
        gr.HTML("""
        <div class="header-container">
            <div>
                <div class="header-title">KPMG <span style="font-weight:400; opacity:0.8;">Market Sizer</span></div>
                <div class="header-subtitle">Intelligence Stratégique & Estimation de Marché</div>
            </div>
            <div style="text-align:right; color: #0091DA; font-family: monospace;">v3.0-FACTS-FIRST</div>
        </div>
        """)
        
        with gr.Tabs():
            
            # ─── ONGLET 1 : ESTIMATION DE MARCHÉ (ENHANCED) ───
            with gr.Tab("📈 Estimation de Marché"):
                gr.Markdown("### 🎯 Définition du Scope & Méthodologie")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Structured Scope Selector
                        gr.Markdown("##### 1. Définir le Périmètre (Scope)")
                        with gr.Row():
                            input_industry = gr.Textbox(label="Industrie / Secteur", placeholder="ex: Logiciels ERP", value="Logiciels de Gestion")
                            input_target = gr.Dropdown(choices=["PME", "ETI", "Grandes Entreprises", "B2C Global", "Niche Spécifique"], label="Cible", value="PME", allow_custom_value=True)
                        
                        with gr.Row():
                            input_region = gr.Dropdown(choices=["Global", "Europe", "France", "Amérique du Nord", "Asie-Pacifique"], label="Zone Géographique", value="France", allow_custom_value=True)
                            input_horizon = gr.Dropdown(choices=["2025", "2026", "2030"], label="Horizon", value="2025", allow_custom_value=True)
                            input_currency = gr.Dropdown(choices=["EUR", "USD", "GBP"], label="Devise", value="EUR")

                        btn_gen_facts = gr.Button("🔍 Analyser & Générer Hypothèses", variant="secondary")
                        btn_calc_est = gr.Button("🧮 Lancer l'Estimation (Triangulation)", variant="primary")
                    
                    with gr.Column(scale=1):
                         gr.Markdown("##### 2. Scénarios (What-If)")
                         slider_price = gr.Slider(minimum=-50, maximum=50, value=0, label="Prix / ARPU (+/- %)", step=5)
                         slider_vol = gr.Slider(minimum=-50, maximum=50, value=0, label="Volume / Clients (+/- %)", step=5)
                         slider_ratio = gr.Slider(minimum=-20, maximum=20, value=0, label="Pénétration (+/- %)", step=1)
                
                # SECTION HYPOTHÈSES (Facts) - REDESIGNED
                gr.Markdown("#### 🏗️ Hypothèses Structurantes (Générées par IA + Validées)")
                out_facts_table = gr.HTML(label="Hypothèses Clés")
                
                # SECTION 0.5: STRATEGIC CONTEXT (Visualizations) - RESTORED
                with gr.Accordion("🧭 Contexte Stratégique (SWOT / BCG / PESTEL)", open=True):
                    with gr.Row():
                        btn_gen_strat = gr.Button("✨ Générer les Matrices Stratégiques", variant="secondary")
                    
                    with gr.Row():
                        with gr.Column():
                            plot_swot = gr.Plot(label="Matrice SWOT")
                        with gr.Column():
                            plot_bcg = gr.Plot(label="Matrice BCG")
                        with gr.Column():
                             plot_pestel = gr.Plot(label="Radar PESTEL")
                
                # SECTION RÉSULTATS (Cards)
                gr.Markdown("### 📊 Résultats de l'Estimation (Triangulation)")
                
                with gr.Row():
                    with gr.Column(scale=1):
                         out_card_macro = gr.HTML()
                    with gr.Column(scale=1):
                         out_card_demand = gr.HTML()
                    with gr.Column(scale=1):
                         out_card_supply = gr.HTML()
                
                # SECTION WATERFALL & SYNTHÈSE
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📉 Entonnoir de Marché (TAM -> SAM -> SOM)")
                        out_waterfall = gr.Plot(label="Cascade de Revenus")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🏁 Estimation Finale Retenue")
                        out_final_decision = gr.HTML()
                
                # SECTION AUDIT
                with gr.Accordion("📂 Audit des Sources & Calculs (Détail)", open=False):
                    out_audit_table = gr.Dataframe(label="Registre Centralisé", interactive=False)

                # HANDLERS
                def generate_hypotheses(ind, tgt, reg, hor, cur):
                    # Construct Scope String
                    scope = f"{ind} pour {tgt} en {reg} (Horizon {hor}) - {cur}"
                    
                    # Call standard generation from SERVICE
                    from strategic_facts_service import strategic_facts_service
                    
                    # Generate facts via LLM
                    gen_facts = strategic_facts_service.generate_market_sizing_facts(scope)
                    
                    # Ingest them into the manager
                    facts_manager.facts_manager.clear_all_facts() # Optional: Clear old facts? Maybe.
                    for f in gen_facts:
                        facts_manager.facts_manager.add_or_update_fact(f)
                        
                    # Refresh Engine to get consolidated view
                    from market_estimation_engine import MarketEstimationEngine
                    engine = MarketEstimationEngine(facts_manager.facts_manager)
                    
                    # Get Raw facts list for HTML generation
                    all_facts = facts_manager.facts_manager.get_facts(category="market_estimation")
                    
                    # HTML GENERATION LOGIC
                    html_content = "<div style='margin-top:10px;'>"
                    
                    for f in all_facts:
                        key_clean = f.get("key", "").replace("_"," ").title()
                        val_display = f"{f.get('value', 'N/A')} {f.get('unit','')}"
                        explanation = f.get("notes", "Aucune explication disponible.")
                        source = f.get("source", "Inconnue")
                        sType = f.get("source_type", "N/A")
                        conf = f.get("confidence", "low").upper()
                        
                        # Confidence Color
                        conf_color = "#00C853" if conf == "HIGH" else "#FFAB00" if conf == "MEDIUM" else "#FF3D00"
                        
                        html_content += f"""
                        <details class="fact-details">
                            <summary class="fact-summary">
                                <span>📌 {key_clean}</span>
                                <span class="fact-value-badge">{val_display}</span>
                            </summary>
                            <div class="fact-content">
                                <div class="fact-explanation">
                                    <div style="font-weight:bold; margin-bottom:5px; color:white;">💡 Explication / Méthode :</div>
                                    {explanation}
                                </div>
                                <div class="fact-metadata">
                                    <div class="meta-row"><span class="meta-label">Source:</span> <span class="meta-val">{source}</span></div>
                                    <div class="meta-row"><span class="meta-label">Type:</span> <span class="meta-val">{sType}</span></div>
                                    <div class="meta-row"><span class="meta-label">Confiance:</span> <span class="meta-val" style="color:{conf_color}">{conf}</span></div>
                                </div>
                            </div>
                        </details>
                        """
                    html_content += "</div>"
                    
                    return html_content
                
                # Restore Strategy Generation Function
                def generate_strategy_matrices(ind, tgt):
                     import analytics_viz
                     # Construct simpler context
                     target_name = f"{ind} ({tgt})"
                     
                     from strategic_facts_service import strategic_facts_service
                     # Ingest strategy facts
                     facts_manager.facts_manager.ingest_strategic_facts(target_name)
                     
                     # Retrieve for viz
                     strat_facts = facts_manager.facts_manager.get_facts(category="strategic_analysis")
                     strategic_data = {"ticker": None, "generated_at": "N/A"}
                     
                     for f in strat_facts:
                        if "swot" in f["key"]: strategic_data["swot"] = f["value"]
                        if "bcg" in f["key"]: strategic_data["bcg"] = f["value"]
                        if "pestel" in f["key"]: strategic_data["pestel"] = f["value"]

                     fig_swot = analytics_viz.generate_swot_from_strategic_facts(strategic_data, target_name)
                     fig_pestel = analytics_viz.generate_pestel_from_strategic_facts(strategic_data, target_name)
                     fig_bcg = analytics_viz.generate_bcg_from_strategic_facts(strategic_data, target_name)
                     
                     return fig_swot, fig_bcg, fig_pestel

                def calculate_estimation(price_adj, vol_adj, ratio_adj):
                    # 1. Prepare Overrides
                    overrides = {}
                    
                    # Fuzzy keys mapping for overrides
                    # We map sliders to canonical keys
                    if price_adj != 0:
                        overrides["average_price"] = 1 + (price_adj / 100.0)
                    
                    if vol_adj != 0:
                        overrides["total_potential_customers"] = 1 + (vol_adj / 100.0)
                    
                    # For ratios, it's additive in points? Or multiplier? 
                    # Let's say simpler: Multiplier on 'sam_percent'
                    if ratio_adj != 0:
                        # If ratio_adj is +5, means +5% growth? Or +5 points?
                        # Let's do Multiplier for consistency 
                        overrides["sam_percent"] = 1 + (ratio_adj / 100.0)

                    # 2. Run Engine with Overrides
                    from market_estimation_engine import MarketEstimationEngine
                    engine = MarketEstimationEngine(facts_manager.facts_manager)
                    
                    best_est = engine.determine_best_method(overrides)
                    all_ests = engine.get_all_estimations(overrides)
                    
                    # 3. Format HTML Cards
                    def format_card(comp):
                        color = comp.color
                        val_str = f"€{comp.estimated_value:,.0f}" if comp.estimated_value else "N/A"
                        status_icon = "✅" if comp.status == "complete" else "⚠️"
                        methodology = comp.methodology_text if hasattr(comp, 'methodology_text') and comp.methodology_text else "Méthode standard non détaillée."
                        
                        # Extract granular reasoning from Facts
                        reasoning_items = []
                        if hasattr(comp, 'data_used') and comp.data_used:
                            for f in comp.data_used:
                                if f.get("notes") and len(f.get("notes")) > 5:
                                    # Clean key for display
                                    clean_key = f.get("key", "").replace("_", " ").title()
                                    reasoning_items.append(f"<li><b>{clean_key}</b> : {f.get('notes')}</li>")
                        
                        reasoning_html = ""
                        if reasoning_items:
                            reasoning_html = f"<ul style='margin: 5px 0 0 15px; padding:0; list-style-type: circle;'>{''.join(reasoning_items)}</ul>"

                        return f"""
                        <div style="border-left: 5px solid {color}; padding: 10px; background: rgba(0,0,0,0.05); border-radius: 5px; margin-bottom: 15px;">
                            <div style="color: {color}; font-weight: bold; font-size: 0.9em;">{comp.name}</div>
                            <div style="font-size: 1.4em; font-weight: bold; margin: 5px 0;">{val_str}</div>
                            <div style="font-size: 0.8em; opacity: 0.8; margin-bottom: 8px;">{comp.method_description}</div>
                            <div style="font-size: 0.7em; margin-bottom: 8px;">{status_icon} {comp.calculation_breakdown}</div>
                            
                            <div style="background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px; font-size: 0.75em; border-left: 2px solid {color};">
                                <b style="color:{color}; opacity:0.9;">📐 Démarche & Méthode :</b><br>
                                <span style="opacity: 0.8; font-style: italic;">"{methodology}"</span>
                                {reasoning_html}
                            </div>
                        </div>
                        """
                    
                    c_macro, c_demand, c_supply, c_tria = all_ests[0], all_ests[1], all_ests[2], all_ests[3]
                    
                    # 4. Waterfall
                    import plotly.graph_objects as go
                    # Use best estimate as TAM base? Or use Macro TAM?
                    # Let's use the Triangulated value as "TAM Global" reference for the waterfall if possible
                    # Or build a standard funnel from TAM -> SAM -> SOM
                    base_val = c_tria.estimated_value if c_tria.estimated_value else 0
                    if base_val == 0 and c_demand.estimated_value: base_val = c_demand.estimated_value
                    
                    df_wf = engine.get_waterfall_data(base_val)
                    fig_wf = go.Figure(go.Waterfall(
                        name = "20", orientation = "v",
                        measure = df_wf["measure"],
                        x = df_wf["x"],
                        textposition = "outside",
                        text = df_wf["text"],
                        y = df_wf["y"],
                        connector = {"line":{"color":"rgb(63, 63, 63)"}},
                        totals = {"marker":{"color":"#00C853"}}
                    ))
                    fig_wf.update_layout(title = "Structure du Marché (Waterfall)", showlegend = False, 
                                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))

                    # 5. Final Decision HTML
                    final_html = f"""
                    <div style="background: linear-gradient(135deg, #6200EA 0%, #3700B3 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        <div style="font-size: 0.8em; text-transform: uppercase;">Estimation Retenue</div>
                        <div style="font-size: 2.2em; font-weight: bold; margin: 10px 0;">€{best_est.estimated_value:,.0f}</div>
                        <div style="font-style: italic; opacity: 0.9;">Méthode : {best_est.selected_strategy_name}</div>
                        <div style="margin-top: 10px; font-size: 0.9em; background: rgba(255,255,255,0.2); padding: 5px; border-radius: 4px;">
                           🎯 Confiance : <b>{best_est.confidence.upper()}</b>
                        </div>
                    </div>
                    """
                    
                    # 6. Audit Table (Refresh to show usage)
                    audit_df = engine.get_consolidated_facts_table()

                    return format_card(c_macro), format_card(c_demand), format_card(c_supply), fig_wf, final_html, audit_df

                btn_gen_facts.click(
                    generate_hypotheses, 
                    inputs=[input_industry, input_target, input_region, input_horizon, input_currency], 
                    outputs=[out_facts_table]
                )
                
                # Trigger calculation on button OR Slider change
                sliders = [slider_price, slider_vol, slider_ratio]
                for s in sliders:
                    s.change(
                        calculate_estimation,
                        inputs=[slider_price, slider_vol, slider_ratio],
                        outputs=[out_card_macro, out_card_demand, out_card_supply, out_waterfall, out_final_decision, out_audit_table]
                    )

                btn_calc_est.click(
                    calculate_estimation,
                    inputs=[slider_price, slider_vol, slider_ratio],
                    outputs=[out_card_macro, out_card_demand, out_card_supply, out_waterfall, out_final_decision, out_audit_table]
                )
                
                # 2. Strategy Generation (Right Button)
                btn_gen_strat.click(
                    generate_strategy_matrices,
                    inputs=[input_industry, input_target],
                    outputs=[plot_swot, plot_bcg, plot_pestel]
                )

            # ─── ONGLET 2 : ANALYSE CONCURRENTIELLE (REVAMPED) ───
            with gr.Tab("⚔️ Analyse Concurrentielle"):
                gr.Markdown("### 🌍 Module d'Intelligence Concurrentielle (Facts-First)")
                
                with gr.Row():
                    btn_comp_run = gr.Button("🚀 Lancer l'Analyse Concurrentielle", variant="primary")
                    # Hidden input to trigger seed if empty
                    comp_status = gr.Textbox(label="Status", value="Ready", visible=False)
                
                # BLOCK 1 & 3: ACTORS & DIFFERENTIATION (Top Layer)
                with gr.Row():
                    with gr.Column(scale=1):
                         gr.Markdown("#### 📦 Bloc 1 : Cartographie des Acteurs")
                         out_actors_summary = gr.Markdown()
                         out_actors_table = gr.Dataframe(label="Typologie des Acteurs", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🎯 Bloc 3 : Positionnement & Différenciation")
                        out_diff_table = gr.Dataframe(label="Clusters de Valeur", interactive=False)

                # BLOCK 2: OFFERINGS (Middle Layer)
                gr.Markdown("#### 🧠 Bloc 2 : Benchmark des Offres (Réalité vs Marketing)")
                out_offerings_matrix = gr.Dataframe(label="Matrice Fonctionnelle", interactive=False)
                
                # BLOCK 4 & 5: DEMAND & RECOMMENDATION (Bottom Layer)
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📣 Bloc 4 : Lecture de la Demande (Gaps)")
                        out_demand_table = gr.Dataframe(label="Attentes Marché", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🧭 Bloc 5 : Recommandation Stratégique")
                        out_rec_html = gr.HTML()

                # SOURCES REGISTER
                gr.Markdown("---")
                gr.Markdown("### 📑 Registre Centralisé des Faits & Sources (Concurrence)")
                out_sources_table = gr.Dataframe(
                    headers=["Variable / Fact", "Valeur", "Source", "Type Source", "Méthode", "Confiance"],
                    label="Audit des Sources Factuelles", 
                    interactive=False,
                    wrap=True
                )

                def run_competitive_analysis():
                    # 1. Ensure Seed Data exists (for demo)
                    facts_manager.facts_manager.generate_competitive_seed_data()
                    
                    # DEBUG: Force Reload of module to prevent stale cache
                    import importlib
                    import competitive_analysis
                    importlib.reload(competitive_analysis)
                    print("🔄 Debug: Competitive Analysis Module Reloaded.")
                    
                    # 2. Instantiate Engine
                    from competitive_analysis import CompetitiveAnalysisEngine
                    engine = CompetitiveAnalysisEngine(facts_manager.facts_manager)
                    
                    # DEBUG: Introspection
                    print(f"🧐 Debug: Engine Methods: {[m for m in dir(engine) if not m.startswith('__')]}")
                    if not hasattr(engine, "get_sources_dataframe"):
                        print("❌ CRITICAL: get_sources_dataframe MISSING from engine instance!")
                    
                    # 3. Execute Blocks
                    # Block 1
                    b1 = engine.analyze_actors()
                    
                    # Block 2
                    b2_df = engine.analyze_offerings()
                    
                    # Block 3
                    b3_df = engine.analyze_differentiation()
                    
                    # Block 4
                    b4 = engine.analyze_demand()
                    
                    # Block 5
                    b5 = engine.recommend_positioning()
                    
                    # Sources Register
                    sources_df = engine.get_sources_dataframe()
                    
                    # Format Block 5 HTML
                    rec_html = f"""
                    <div style="background: linear-gradient(135deg, #00C853 0%, #009624 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div style="font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8;">Recommandation Prioritaire</div>
                        <div style="font-size: 1.5em; font-weight: bold; margin: 10px 0;">{b5['strategy_title']}</div>
                        <div style="font-style: italic; opacity: 0.9; margin-bottom: 15px;">"{b5['rationale']}"</div>
                        <div style="background: rgba(0,0,0,0.2); padding: 5px 10px; border-radius: 4px; font-size: 0.9em;">
                            🚫 <b>À éviter :</b> {b5['avoid']}
                        </div>
                    </div>
                    """
                    
                    return (
                        b1["summary_text"], 
                        b1["actors_table"], 
                        b3_df, 
                        b2_df, 
                        b4["expectations_table"], 
                        rec_html,
                        sources_df
                    )

                btn_comp_run.click(
                    run_competitive_analysis,
                    inputs=None,
                    outputs=[out_actors_summary, out_actors_table, out_diff_table, out_offerings_matrix, out_demand_table, out_rec_html, out_sources_table]
                )

            # ─── ONGLET 3 : CHAT STRATÉGIQUE (Conservé pour support) ───
            with gr.Tab("💬 Assistant & Sources"):
                 with gr.Row():
                     with gr.Column():
                         gr.Markdown("### 🧠 Assistant Méthodologique\nPosez des questions sur les sources ou la méthode.")
                         gr.ChatInterface(fn=rag_stream_function)

    # Monkey patch launch() to default include theme and css
    # This solves the depreciation warning while keeping the specialized KPMG branding by default
    original_launch = demo.launch
    def launch_with_theme(*args, **kwargs):
        if "theme" not in kwargs: kwargs["theme"] = theme
        if "css" not in kwargs: kwargs["css"] = custom_css
        return original_launch(*args, **kwargs)
    
    demo.launch = launch_with_theme
    
    # Launch the dashboard
    demo.launch(share=False)
    
    return demo

if __name__ == "__main__":
    # Mock des fonctions externes pour test direct
    def mock_rag(msg, hist): return "Ceci est une réponse simulée."
    demo = launch_dashboard(mock_rag)
    demo.launch()