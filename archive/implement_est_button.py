
import os

file_path = "/Users/robincrifo/Documents/KPMG/kpmg/HACK-KPMG/kpmg_interface.py"

with open(file_path, 'r') as f:
    content = f.read()

# 1. RENAME BUTTON
# Locate 'btn_load_context'
# btn_load_context = gr.Button("📊 Charger Données Fin.", variant="secondary", scale=1)

start_btn = content.find('btn_load_context = gr.Button')
if start_btn == -1:
    print("Could not find button definition")
    exit(1)

# Renaming to:
# btn_estimate = gr.Button("🚀 Lancer l'Estimation de Marché", variant="primary", scale=1)
# btn_gen_strat = gr.Button("✨ Analyser la Stratégie (Matrices)", variant="secondary", scale=1)

lines = content.splitlines()
idx_btn = -1
for i, line in enumerate(lines):
    if 'btn_load_context = gr.Button' in line:
        idx_btn = i
        break

if idx_btn != -1:
    indent = lines[idx_btn][:lines[idx_btn].find('btn_load_context')]
    lines[idx_btn] = f'{indent}btn_estimate = gr.Button("🚀 Lancer l\'Estimation", variant="primary", scale=1)'
    # The next line should be btn_gen_strat already, update variant to secondary to contrast
    lines[idx_btn + 1] = f'{indent}btn_gen_strat = gr.Button("✨ Analyser la Stratégie", variant="secondary", scale=1)'
else:
    print("Error locating button lines")

# 2. DEFINE NEW FUNCTION run_estimation_sequence
# This function handles the "Left Button":
# - If Ticker: Load Financials
# - ALWAYS: Generate Market Sizing Facts (Mistral) based on scope (if missing or force refresh) -- Wait, user wants "Lancer Estimation".
# This implies generating the foundational numbers (TAM/SAM/SOM) from the LLM if they are not manual inputs.
# Let's use `strategic_facts_service.generate_market_sizing_facts`

# We replace `load_financials_only` with `run_full_market_estimation`.

logic_code = """                # SPLIT LOGIC: 1. Estimation (Market), 2. Strategy (Matrices)

                # Helper to reload manager
                def _reload_manager():
                    import importlib
                    import facts_manager
                    importlib.reload(facts_manager)
                    return facts_manager.facts_manager

                def run_full_market_estimation(ticker_ref, industry, region, horizon, currency):
                    print(f"DEBUG: Running Full Estimation for {industry} in {region}...")
                    mgr = _reload_manager()
                    
                    # 1. Define Scope
                    scope_str = f"{industry} en {region} (Horizon {horizon}) - {currency}"
                    mgr.set_market_scope(scope_str)
                    
                    # 2. Ingest Financials ONLY IF Ticker is present (Optional)
                    if ticker_ref:
                        print(f"   + Ingesting Financials for {ticker_ref}")
                        try:
                            mgr.ingest_financial_facts(ticker_ref)
                        except Exception as e:
                            print(f"⚠️ Financial Ingestion Error: {e}")
                    
                    # 3. Generate Market Sizing Facts (Mistral) - THE CORE ESTIMATION
                    # This replaces the need for manual input of TAM/SAM
                    from strategic_facts_service import strategic_facts_service
                    print(f"   + Generating Market Sizing Facts via LLM for: {scope_str}")
                    strategic_facts_service.generate_market_sizing_facts(scope_str)
                    
                    # 4. Refresh Inputs from Manager (so UI sliders might update if we mapped them back, 
                    # but here we return values to update the UI components)
                    
                    tam_val = mgr.get_fact_value("tam_global_market", 0)
                    sam_val = mgr.get_fact_value("sam_percent", 20)
                    som_val = mgr.get_fact_value("som_share", 5)
                    
                    # Scale fix
                    if sam_val < 1 and sam_val > 0: sam_val = sam_val * 100
                    if som_val < 1 and som_val > 0: som_val = som_val * 100
                    
                    # Also trigger competitors search? Maybe too heavy?
                    # Let's do it to be complete "Lancer Estimation"
                    try:
                        competitors = strategic_facts_service.find_competitors(scope_str)
                        # Maybe ingest one or two?
                    except:
                        pass
                        
                    return tam_val, sam_val, som_val

                def generate_strategy_matrices(ticker_ref, industry_context):
                    # Existing logic... keeping as is or ensure it is preserved 
                    # (Code below copies it to ensure order)
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
                        import plotly.graph_objects as go
                        err = go.Figure().add_annotation(text=f"Error: {e}", showarrow=False, font=dict(color="red"))
                        return err, err, err
"""

# Replace the functions block
# Start: `def load_financials_only(ticker_ref):`
# End: Just before `bind_load_context.click` (Wait, we renamed bindings too?) - The bindings loop logic is safest.

idx_def_start = -1
for i, line in enumerate(lines):
    if "def load_financials_only(ticker_ref):" in line:
        idx_def_start = i
        break

# We need to find the end of `generate_strategy_matrices` (which was added previously)
# Actually, we can just replace from `load_financials_only` start up to bindings start.

idx_bindings = -1
for i, line in enumerate(lines):
    if "# Bindings" in line:
        idx_bindings = i
        break

if idx_def_start == -1 or idx_bindings == -1:
    print("Could not find function bounds (step 2)")
    exit(1)

# Replace block
# Careful of `_reload_manager` def if it was there.
if "def _reload_manager():" in lines[idx_def_start-5:idx_def_start]: # Check above
     # It might be there from previous script. 
     # `logic_code` includes `_reload_manager` again. 
     # To avoid duplication, let's find the start of `_reload_manager` instead.
     for j in range(idx_def_start-10, idx_def_start):
         if "def _reload_manager():" in lines[j]:
             idx_def_start = j
             break

lines[idx_def_start:idx_bindings] = logic_code.splitlines()

# 3. UPDATE BINDINGS
# btn_load_context is gone, now btn_estimate
# btn_gen_strat remains

new_bindings = """                # Bindings
                
                # 1. Market Estimation (Left Button)
                # Triggers LLM generation of facts -> Updates Inputs -> Triggers Calculation
                btn_estimate.click(
                    run_full_market_estimation,
                    inputs=[context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[tam_input, sam_pct_input, som_share_input]
                ).success(
                    refresh_market_sizing,
                    inputs=[scenario_radio, tam_input, sam_pct_input, som_share_input, context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[plot_waterfall, plot_football, facts_display, sources_table]
                )

                # 2. Strategy Generation (Right Button)
                btn_gen_strat.click(
                    generate_strategy_matrices,
                    inputs=[context_ticker, input_industry],
                    outputs=[plot_swot, plot_bcg, plot_pestel]
                )
"""

# Find binding block start/end
idx_bind_end = -1
for i in range(idx_bindings, len(lines)):
    if "def load_initial_state():" in lines[i]:
        idx_bind_end = i
        break

lines[idx_bindings:idx_bind_end] = new_bindings.splitlines()

# WRITE BACK
with open(file_path, 'w') as f:
    f.write("\n".join(lines))

print("File updated: Market Estimation button implemented.")
