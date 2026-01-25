
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
    .card-panel {
        background: #1E1E1E !important; border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important; padding: 1rem !important;
    }
    .fact-card {
        background: rgba(0, 145, 218, 0.1); border-left: 3px solid #0091DA;
        padding: 10px; margin-bottom: 10px; border-radius: 4px;
    }
    .missing-fact {
        background: rgba(255, 61, 0, 0.1); border-left: 3px solid #FF3D00;
        padding: 10px; margin-bottom: 10px; border-radius: 4px; border: 1px dashed #FF3D00;
    }
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
            
            # ─── ONGLET 1 : ESTIMATION DU MARCHÉ ───
            with gr.Tab("🎯 Estimation du Marché"):
                
                # SECTION 0: CONTEXT SELECTION
                # SECTION 0: SCOPE SELECTOR (CB INSIGHTS STYLE)
                gr.Markdown("### 🎯 Définition du Périmètre")
                with gr.Row():
                    input_industry = gr.Textbox(label="Industrie / Secteur", placeholder="ex: Logiciels ERP", value="Logiciels de Gestion PME", scale=2)
                    input_region = gr.Dropdown(choices=["Global", "Europe", "France", "USA", "Asie"], label="Zone", value="France", allow_custom_value=True, scale=1)
                    input_horizon = gr.Dropdown(choices=["2024", "2025", "2030"], label="Horizon", value="2025", allow_custom_value=True, scale=1)
                    input_currency = gr.Dropdown(choices=["EUR", "USD", "GBP"], label="Devise", value="EUR", scale=0)
                
                with gr.Row():
                    context_ticker = gr.Textbox(label="Ticker de Référence (Contexte)", value="", placeholder="Optionnel (ex: AAPL)", scale=2)
                    btn_estimate = gr.Button("🚀 Lancer l'Estimation", variant="primary", scale=1)
                    btn_gen_strat = gr.Button("✨ Analyser la Stratégie", variant="secondary", scale=1)
                    # Hidden or removed save button as scope is auto-constructed? Keeping it hidden for legacy compat
                    btn_save_scope = gr.Button("💾", scale=0, min_width=50, visible=False)

                # SECTION 0.5: STRATEGIC CONTEXT (Visualizations)
                gr.Markdown("### 🧭 Contexte Stratégique (SWOT / BCG / PESTEL)")
                with gr.Row():
                    with gr.Column():
                        plot_swot = gr.Plot(label="Matrice SWOT")
                    with gr.Column():
                        plot_bcg = gr.Plot(label="Matrice BCG")
                    with gr.Column():
                         plot_pestel = gr.Plot(label="Radar PESTEL")

                # SECTION 1: EXEC SUMMARY & SCENARIOS
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 Synthèse de l'Estimation (TAM / SAM / SOM)")
                        plot_waterfall = gr.Plot(label="Market Waterfall")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎛️ Paramètres & Scénarios")
                        with gr.Group():
                            scenario_radio = gr.Radio(["Pessimiste", "Base", "Optimiste"], value="Base", label="Scénario Actif")
                            tam_input = gr.Number(label="TAM Global Market (€)", value=0)
                            sam_pct_input = gr.Slider(0, 100, label="% SAM (Addressable)", value=20)
                            som_share_input = gr.Slider(0, 100, label="% SOM (Target Share)", value=5)
                            
                            # MANUAL INDICATORS OVERRIDE
                            with gr.Accordion("⚙️ Ajuster les Indicateurs (Manuel)", open=False):
                                gr.Markdown("Modifiez les hypothèses de base (Volumes, Prix, etc.)")
                                manual_indicators_input = gr.Dataframe(
                                    headers=["Clé", "Valeur", "Unité"],
                                    datatype=["str", "number", "str"],
                                    column_count=(3, "fixed"),
                                    interactive=True,
                                    label="Indicateurs Clés",
                                    value=[["target_volume", 0, "clients"], ["unit_price", 0, "EUR"]]
                                )
                                btn_calc = gr.Button("🔄 Recalculer avec mes ajustements", variant="primary")
                            
                            # FOOTBALL FIELD
                            gr.Markdown("#### 📐 Triangulation")
                            plot_football = gr.Plot(label="Football Field")

                # SECTION 0: SCOPE DEFINITION (NEW)
                scope_display = gr.HTML()

                # SECTION 1: HERO METRICS (Now below Scope)
                with gr.Row():
                    # ... (Existing Hero) ...
                    pass

                # SECTION 2: HYPOTHESES & MISSING FACTS
                gr.Markdown("---")
                with gr.Row():
                    with gr.Column(scale=1):
                         gr.Markdown("### 💡 Hypothèses & Sources (Résumé)")
                         facts_display = gr.HTML()
                    
                    # You can add other summary widgets here if needed
                
                # SECTION 3: CENTRALIZED AUDIT TABLE
                gr.Markdown("---")
                gr.Markdown("### 📑 Registre Centralisé des Faits & Sources (Audit)")
                with gr.Row():
                    sources_table = gr.Dataframe(
                        headers=["Variable / Fact", "Valeur", "Source", "Type Source", "Méthode", "Confiance", "Utilisé dans"],
                        interactive=False,
                        wrap=True,
                        column_widths=["15%", "10%", "15%", "15%", "15%", "10%", "20%"] 
                    )



                # LOGIQUE MARKET SIZING (UPDATED FOR GRANULARITY)
                def refresh_market_sizing(scenario, tam_val, sam_pct, som_pct, manual_data, ticker_ref, industry, region, horizon, currency):
                    # Construct Scope String dynamically
                    scope_str = f"{industry} en {region} (Horizon {horizon}) - {currency}"
                    facts_manager.facts_manager.set_market_scope(scope_str)

                    # 0. INGEST MANUAL OVERRIDES
                    if manual_data is not None:
                         # Type Guard for binding mismatches
                         if isinstance(manual_data, str):
                             print(f"⚠️ ARGUMENT MISMATCH: manual_data received string '{manual_data}' instead of DataFrame. Ignoring.")
                         elif not manual_data.empty:
                             print("📝 Ingesting Manual Indicators...")
                             for _, row in manual_data.iterrows():
                                  key = row[0]
                                  try:
                                      val = float(row[1])
                                      unit = row[2]
                                      if val > 0: # Only ingest meaningful overrides
                                          facts_manager.facts_manager.add_or_update_fact({
                                              "key": key,
                                              "value": val,
                                              "unit": unit,
                                              "source": "Utilisateur (Manuel)",
                                              "source_type": "Primaire",
                                              "confidence": "high"
                                          })
                                  except:
                                      pass

                    # 1. Update Temporary Facts from Inputs (Macro)
                    try:
                        facts_manager.facts_manager.add_or_update_fact({"key": "tam_global_market", "value": tam_val, "category": "market_estimation"})
                        facts_manager.facts_manager.add_or_update_fact({"key": "sam_percent", "value": sam_pct, "category": "market_estimation"})
                        facts_manager.facts_manager.add_or_update_fact({"key": "som_share", "value": som_pct, "category": "market_estimation"})
                    except:
                        pass # Handle potential reload issues gracefully

                    # 2. Run Engine (Now supports Granular Strategies)
                    from market_estimation_engine import MarketEstimationEngine
                    engine = MarketEstimationEngine(facts_manager.facts_manager)
                    
                    estimations = engine.get_all_estimations()
                    
                    # Consolidated table
                    sources_df = engine.get_consolidated_facts_table()

                    # Determine Best Method
                    best_comp = engine.determine_best_method()
                    
                    # 3. Generate HTML for 4 Components (UPDATED SCOPE DISPLAY)
                    
                    # 3.1 Scope Display Generation
                    scope_def = facts_manager.facts_manager.get_fact_value("market_scope_definition", None)
                    scope_html_content = ""
                    if scope_def:
                        scope_html_content = f"""
                        <div style="background: rgba(33, 150, 243, 0.1); border-left: 5px solid #2196F3; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                            <h4 style="margin-top:0; color: #BBDEFB;">🎯 Scope Défini (Périmètre Explicite)</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em; color: #E0E0E0;">
                                <div><b>Type :</b> {scope_def.get('market_type', 'N/A')}</div>
                                <div><b>Modèle Rev :</b> {scope_def.get('revenue_model', 'N/A')}</div>
                                <div><b>Unité Eco :</b> {scope_def.get('economic_unit', 'N/A')}</div>
                                <div><b>Cible :</b> {scope_def.get('target_clients', 'N/A')}</div>
                            </div>
                            <div style="margin-top: 10px; font-size: 0.9em;">
                                <span style="color: #66BB6A;">✅ Inclus : {', '.join(scope_def.get('products_included', []))}</span><br>
                                <span style="color: #EF5350;">❌ Exclu : {', '.join(scope_def.get('products_excluded', []))}</span>
                            </div>
                        </div>
                        """
                    else:
                        scope_html_content = "<div style='color:gray; font-style:italic;'>Scope non défini. Lancez l'estimation.</div>"


                    
                    # HERO INSIGHT (CB INSIGHTS STYLE)
                    hero_val = "N/A"
                    if best_comp.estimated_value:
                        hero_val = format_currency(best_comp.estimated_value)
                        
                    # Confidence Color
                    conf_color = "#4CAF50" # Green for High
                    if best_comp.confidence == "medium": conf_color = "#FF9800"
                    if best_comp.confidence == "low": conf_color = "#F44336"
                    
                    decision_html = f'''
                    <div style="background: linear-gradient(135deg, #1A237E 0%, #0D47A1 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); text-align: center; border: 1px solid rgba(255,255,255,0.1);">
                        
                        <div style="font-size: 0.9em; text-transform: uppercase; letter-spacing: 2px; color: #BBDEFB; margin-bottom: 10px;">
                            ESTIMATION DE MARCHÉ RETENUE
                        </div>
                        
                        <div style="font-size: 4.5em; font-weight: 800; color: white; line-height: 1.1; text-shadow: 0 0 20px rgba(33, 150, 243, 0.5);">
                            {hero_val}
                        </div>
                        
                        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 20px;">
                            <div style="background: {conf_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                                CONFIANCE {best_comp.confidence.upper()}
                            </div>
                            <div style="color: #E3F2FD; font-size: 1.1em;">
                                Basé sur : <b>{best_comp.name}</b>
                            </div>
                        </div>

                        <div style="margin-top: 25px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; color: #90CAF9; font-style: italic; max-width: 600px; margin-left: auto; margin-right: auto;">
                            "{best_comp.role}"
                        </div>
                    </div>
                    
                    <h3 style="margin-bottom: 20px; color: #E0E0E0; border-left: 4px solid #BBDEFB; padding-left: 10px;">🔍 Analyse Méthodologique Détaillée (Audit Log)</h3>
                    '''
                    
                    # CALL NEW AUDIT COMPONENT
                    from kpmg_audit_component import generate_audit_component_html
                    audit_html = generate_audit_component_html(engine, best_comp, facts_manager.facts_manager)
                    
                    html_content = decision_html + audit_html
                    
                    # 4. Generate Visualizations (Responsive to Best Method)
                    
                    # 4.1 Waterfall (TAM -> SAM -> SOM)
                    # Use the Best TAM as base
                    base_tam = best_comp.estimated_value if best_comp.estimated_value else 0
                    
                    # Retrieve SAM/SOM ratios (from facts)
                    # Note: Facts stores decimals (0.20) or integers? 
                    # Engine conversion to float usually happens in logic.
                    # Let's trust FactsManager to return what was stored.
                    # Previous step stored 0.20 for 20%.
                    
                    f_sam = facts_manager.facts_manager.get_fact_value("sam_percent", 0.2)
                    f_som = facts_manager.facts_manager.get_fact_value("som_share", 0.05)
                    
                    # Ensure they are ratios <= 1. If > 1, assume percentage and divide.
                    if f_sam > 1: f_sam /= 100.0
                    if f_som > 1: f_som /= 100.0
                    
                    calc_sam = base_tam * f_sam
                    calc_som = calc_sam * f_som # SOM is usually share of SAM or share of TAM? 
                    # Definition in prompt: "SOM (Serviceable Obtainable Market) : Part de marché capturable à court terme (en % du SAM)."
                    # So SOM = SAM * SOM%
                    
                    fig_waterfall = analytics_viz.plot_market_sizing_waterfall(base_tam, calc_sam, calc_som, currency)
                    
                    # 4.2 Football Field (Method Comparison)
                    # Convert estimations to ranges
                    ranges = []
                    for comp in estimations:
                        if comp.estimated_value is not None and comp.estimated_value > 0:
                            # Create an artificial range +/- 20% for 'estimation' type, or 0 for precise
                            # Improve: Use confidence to dictate range?
                            width = 0.20 # Default +/- 20%
                            if comp.confidence == "high": width = 0.10
                            if comp.confidence == "low": width = 0.40
                            
                            val = comp.estimated_value
                            r_min = val * (1 - width)
                            r_max = val * (1 + width)
                            
                            ranges.append({
                                "label": comp.name.replace("Estimation ", ""),
                                "min": r_min,
                                "max": r_max,
                                "val": val
                            })
                    
                    fig_football = analytics_viz.plot_valuation_football_field(ranges)

                    return fig_waterfall, fig_football, html_content, sources_df, scope_html_content
                 
                 # Bindings Update needed to ensure outputs match
                 # refresh_market_sizing outputs 4 items: [plot_waterfall, plot_football, facts_display, sources_table]
                 # Wait, 'decision_html' goes to 'facts_display' (HTML component).
                 
                 # Verify function signature in binding:
                 # outputs=[plot_waterfall, plot_football, facts_display, sources_table]
                 # My return: fig_waterfall, fig_football, html_content, sources_df
                 # Matches perfectly.
                # Function to save scope
                def save_scope_action(new_scope):
                    print(f"DEBUG: Saving scope: {new_scope}")
                    try:
                        facts_manager.facts_manager.set_market_scope(new_scope)
                        return f"Portée mise à jour : {new_scope}"
                    except Exception as e:
                        print("❌ ERROR in save_scope_action:")
                        traceback.print_exc()
                        return "Erreur Save"

                # LOAD STRATEGIC CONTEXT + FINANCIALS
                # SPLIT LOGIC: 1. Financials, 2. Strategy

                # Helper to reload manager
                def _reload_manager():
                    import importlib
                    import facts_manager
                    importlib.reload(facts_manager)
                    return facts_manager.facts_manager

                # SPLIT LOGIC: 1. Estimation (Market), 2. Strategy (Matrices)

                # Helper to reload manager
                def _reload_manager():
                    import importlib
                    import facts_manager
                    importlib.reload(facts_manager)
                    return facts_manager.facts_manager

                def run_full_market_estimation(ticker_ref, industry, region, horizon, currency):
                    # CONSOLE DEBUG
                    print(f"\n🚀 [DEBUG] STARTING MARKET ESTIMATION")
                    print(f"   - Inputs: Ind='{industry}', Reg='{region}', Hor='{horizon}', Cur='{currency}'")
                    
                    mgr = _reload_manager()
                    
                    # 1. Define Scope
                    scope_str = f"{industry} en {region} (Horizon {horizon}) - {currency}"
                    print(f"   - Generated Scope: '{scope_str}'")
                    
                    # UI DEBUG TOAST
                    gr.Info(f"🛠️ DEBUG: Nouveau Scope généré : {scope_str}")
                    
                    mgr.set_market_scope(scope_str)
                    
                    # 2. Ingest Financials ONLY IF Ticker is present
                    if ticker_ref:
                        print(f"   - Ingesting Financials for {ticker_ref}")
                        try:
                            mgr.ingest_financial_facts(ticker_ref)
                        except Exception as e:
                            print(f"   ⚠️ Financial Ingestion Error: {e}")
                    
                    # 3. Generate Market Sizing Facts (Mistral)
                    from strategic_facts_service import strategic_facts_service
                    print(f"   - Calling LLM for Market Sizing Facts...")
                    
                    # Force FRESH generation by calling service
                    new_facts = strategic_facts_service.generate_market_sizing_facts(scope_str)
                    print(f"   ✅ LLM returned {len(new_facts)} facts:")
                    for f in new_facts:
                         print(f"      -> {f['key']}: {f['value']} ({f.get('source', 'No Source')})")
                         # CRITICAL FIX: Inject into Manager
                         mgr.add_or_update_fact(f)
                    
                    # 4. Refresh Inputs from Manager
                    tam_val = mgr.get_fact_value("tam_global_market", 0)
                    sam_val = mgr.get_fact_value("sam_percent", 20)
                    som_val = mgr.get_fact_value("som_share", 5)
                    
                    print(f"   - Updated Manager Values: TAM={tam_val}, SAM={sam_val}, SOM={som_val}")
                    
                    # Scale fix
                    if sam_val < 1 and sam_val > 0: sam_val = sam_val * 100
                    if som_val < 1 and som_val > 0: som_val = som_val * 100
                    
                    # Competitors Search
                    try:
                        competitors = strategic_facts_service.find_competitors(scope_str)
                    except:
                        pass
                        
                    # PRINT FULL FACTS TABLE (DEBUG REQUEST)
                    print("\n📊 [DEBUG] FINAL FACTS TABLE STATE:")
                    print(mgr.get_all_facts_as_dataframe().to_string())
                    print("--------------------------------------------------\n")
                    
                    # Prepare Manual Indicators DataFrame from Generated Facts
                    inds = []
                    keys_of_interest = ["target_volume", "unit_price", "top_players_cumulative_revenue", "market_multiplier_factor", "production_volume", "average_unit_market_value"]
                    
                    for k in keys_of_interest:
                        f = mgr.get_facts(k) # Use get_fact to get unit/value
                        if f:
                            inds.append([k, f.get("value"), f.get("unit", "N/A")])
                    
                    # If empty, add defaults
                    if not inds:
                        inds = [["target_volume", 0, "clients"], ["unit_price", 0, "EUR"]]
                        
                    return tam_val, sam_val, som_val, inds

                def generate_strategy_matrices(ticker_ref, industry_context):
                    print(f"DEBUG: Generating Strategy Matrices for {ticker_ref} or {industry_context}...")
                    try:
                        mgr = _reload_manager()
                        target_name = ticker_ref if ticker_ref else industry_context
                        if not target_name: target_name = "Acteur Générique"
                        tik = ticker_ref if ticker_ref else None
                        
                        print(f"🔄 Syncing strategy for {target_name}...")
                        mgr.ingest_strategic_facts(target_name, tik)
                        
                        strat_facts = mgr.get_facts(category="strategic_analysis")
                        strategic_data = {"ticker": tik, "generated_at": "N/A"}
                        swot_found = False
                        
                        for f in strat_facts:
                            if "swot" in f["key"]: 
                                strategic_data["swot"] = f["value"]
                                swot_found = True
                            if "bcg" in f["key"]: strategic_data["bcg"] = f["value"]
                            if "pestel" in f["key"]: strategic_data["pestel"] = f["value"]
                            if "source" in f: strategic_data["generated_at"] = f.get("source")

                        if not swot_found:
                             import plotly.graph_objects as go
                             empty = go.Figure().add_annotation(text="Données non trouvées.", showarrow=False)
                             return empty, empty, empty
                        
                        fig_swot = analytics_viz.generate_swot_from_strategic_facts(strategic_data, target_name)
                        fig_pestel = analytics_viz.generate_pestel_from_strategic_facts(strategic_data, target_name)
                        fig_bcg = analytics_viz.generate_bcg_from_strategic_facts(strategic_data, target_name)
                        
                        return fig_swot, fig_bcg, fig_pestel

                    except Exception as e:
                        print(f"❌ Error Strategy: {e}")
                        import traceback
                        traceback.print_exc()
                        import plotly.graph_objects as go
                        err = go.Figure().add_annotation(text=f"Error: {e}", showarrow=False, font=dict(color="red"))
                        return err, err, err

                # Bindings
                
                # 1. Market Estimation (Left Button)
                # Triggers LLM generation of facts -> Updates Inputs -> Triggers Calculation
                btn_estimate.click(
                    run_full_market_estimation,
                    inputs=[context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[tam_input, sam_pct_input, som_share_input, manual_indicators_input]
                ).success(
                    refresh_market_sizing,
                    inputs=[scenario_radio, tam_input, sam_pct_input, som_share_input, manual_indicators_input, context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[plot_waterfall, plot_football, facts_display, sources_table, scope_display] # ADDED scope_display
                )

                # Recalculate Button (Manual)
                btn_calc.click(
                    refresh_market_sizing,
                    inputs=[scenario_radio, tam_input, sam_pct_input, som_share_input, manual_indicators_input, context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[plot_waterfall, plot_football, facts_display, sources_table, scope_display]
                )
                
                # 2. Strategy Generation (Right Button)
                btn_gen_strat.click(
                    generate_strategy_matrices,
                    inputs=[context_ticker, input_industry],
                    outputs=[plot_swot, plot_bcg, plot_pestel]
                )
                def load_initial_state():
                    print("🚀 NOUVELLE SESSION : Nettoyage et Génération des Facts...")
                    
                    # 1. Clear previous session facts
                    facts_manager.facts_manager.clear_all_facts()
                    
                    # 2. Define defaults
                    def_ind = "Logiciels de Gestion (ERP/CRM) pour PME"
                    def_reg = "France"
                    def_hor = "2025"
                    def_cur = "EUR"
                    default_ticker = "" # Optional by default
                    
                    default_scope = f"{def_ind} en {def_reg} - {def_hor}"
                    
                    # 3. Store Context Fact
                    facts_manager.facts_manager.set_market_scope(default_scope)
                    
                    # 4. Generate Market Sizing Facts (Mistral)
                    from strategic_facts_service import strategic_facts_service
                    
                    gen_facts = strategic_facts_service.generate_market_sizing_facts(default_scope)
                    for f in gen_facts:
                        facts_manager.facts_manager.add_or_update_fact(f)

                    # 5. Massive Data Harvest (Competitors)
                    print("🚜 [HARVEST] Démarrage de la moisson de données concurrentielles...")
                    try:
                        competitors = strategic_facts_service.find_competitors(default_scope)
                        # Add main ticker if specified
                        if default_ticker:
                            competitors.append(default_ticker)
                        
                        competitors = list(set(competitors)) # Dedup
                        
                        count = 0
                        for comp_ticker in competitors:
                            print(f"   ⬇️ Ingestion financière : {comp_ticker}")
                            facts_manager.facts_manager.ingest_financial_facts(comp_ticker)
                            count += 1
                        
                        print(f"✅ [HARVEST] {count} concurrents scannés et ingérés.")
                    except Exception as e:
                        print(f"⚠️ [HARVEST] Erreur partielle : {e}")

                    # 6. Fetch values for UI
                    tam = facts_manager.facts_manager.get_fact_value("tam_global_market", 0)
                    sam = facts_manager.facts_manager.get_fact_value("sam_percent", 0.20)
                    som = facts_manager.facts_manager.get_fact_value("som_share", 0.05)
                    
                    if sam <= 1: sam = sam * 100
                    if som <= 1: som = som * 100
                    
                    print(f"✅ Session initialisée avec succès. Total Facts: {len(facts_manager.facts_manager.facts)}")
                    # Return separated defaults for inputs
                    return def_ind, def_reg, def_hor, def_cur, default_ticker, tam, sam, som

                # Setup initial load
                demo.load(
                     load_initial_state, 
                     inputs=None,
                     outputs=[input_industry, input_region, input_horizon, input_currency, context_ticker, tam_input, sam_pct_input, som_share_input]
                ).then(
                    refresh_market_sizing,
                    inputs=[scenario_radio, tam_input, sam_pct_input, som_share_input, manual_indicators_input, context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[plot_waterfall, plot_football, facts_display, sources_table, scope_display] # ADDED scope_display
                )
                
                # Removed redundant btn_calc.click() binding that had wrong arguments

                
                # Save scope on click or blur (Disabled or Removed)
                # btn_save_scope.click(...)

            # ─── ONGLET 2 : ANALYSE CONCURRENTIELLE ───
            with gr.Tab("⚔️ Analyse Concurrentielle"):
                gr.Markdown("### 🌍 Paysage Concurrentiel & Positionnement")
                
                with gr.Row():
                    with gr.Column(scale=1):
                         # Configuration
                         comp_company_input = gr.Textbox(label="Entreprise Cible", value="Tesla")
                         btn_comp_gen = gr.Button("🔎 Scanner la Concurrence", variant="primary")
                         
                         gr.Markdown("#### 📋 Liste des Concurrents (Facts)")
                         comp_list_html = gr.HTML()
                    
                    with gr.Column(scale=2):
                        # Matrice Positionnement
                        plot_positioning = gr.Plot(label="Positionnement Prix/Valeur")
                
                gr.Markdown("---")
                gr.Markdown("### 📊 Comparatif Fonctionnel & Financier")
                comp_table = gr.Dataframe(
                    headers=["Concurrent", "Revenus", "Part de Marché", "Différenciateur", "Menace"],
                    datatype=["str", "number", "str", "str", "str"],
                    interactive=False
                )
                
                def update_competition(company):
                    # 1. Get Strategic facts (SWOT/BCG/PESTEL) just to have some context or use new logic
                    # For competition specifically, we might need a specific call or mocks
                    # Let's mock a competition landscape based on the company name
                    
                    # Mock logic for demo "Facts-First"
                    competitors = facts_manager.facts_manager.get_fact_value("competitor_list", ["Comp A", "Comp B"])
                    
                    # Generate a positioning matrix (Mock)
                    # X axis: Price, Y axis: Quality
                    import plotly.express as px
                    df_comp = pd.DataFrame([
                        {"Name": company, "Price": 8, "Quality": 9, "Type": "Target"},
                        {"Name": "Competitor A", "Price": 6, "Quality": 7, "Type": "Direct"},
                        {"Name": "Competitor B", "Price": 9, "Quality": 8, "Type": "Premium"},
                        {"Name": "Competitor C", "Price": 4, "Quality": 5, "Type": "Low-Cost"},
                    ])
                    
                    fig_pos = px.scatter(df_comp, x="Price", y="Quality", color="Type", text="Name", 
                                         size=[30, 20, 20, 20], title="Matrice Prix / Valeur Percecue")
                    fig_pos.update_traces(textposition='top center')
                    fig_pos.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                                          font=dict(color="white"))
                    fig_pos.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', range=[0, 10])
                    fig_pos.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', range=[0, 10])

                    # HTML List
                    list_html = "<ul>"
                    for c in competitors:
                        list_html += f"<li><b>{c}</b> <span style='color:orange'>[Fact Check Required]</span></li>"
                    list_html += "</ul>"
                    
                    # Table
                    df_table = pd.DataFrame([
                        [company, 95000000, "15%", "Innovation", "N/A"],
                        ["Competitor A", 50000000, "8%", "Prix", "High"],
                        ["Competitor B", 80000000, "12%", "Service", "Medium"],
                    ], columns=["Concurrent", "Revenus", "Part de Marché", "Différenciateur", "Menace"])

                    return list_html, fig_pos, df_table

                btn_comp_gen.click(update_competition, inputs=[comp_company_input], outputs=[comp_list_html, plot_positioning, comp_table])

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