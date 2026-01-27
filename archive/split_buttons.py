
import os

file_path = "/Users/robincrifo/Documents/KPMG/kpmg/HACK-KPMG/kpmg_interface.py"

with open(file_path, 'r') as f:
    content = f.read()

# 1. ADD NEW BUTTON
# Locate 'btn_load_context' definition
# 94:                     context_ticker = gr.Textbox(label="Ticker de Référence (Contexte)", value="", placeholder="Optionnel (ex: AAPL)", scale=2)
# 95:                     btn_load_context = gr.Button("📂 Charger Facts & Stratégie", variant="secondary", scale=1)

start_btn = content.find('btn_load_context = gr.Button("📂 Charger Facts & Stratégie"')
if start_btn == -1:
    print("Could not find button definition")
    exit(1)

# Renaming logic
# We want to change the line to:
# btn_load_context = gr.Button("📊 Charger Données Financières", variant="secondary", scale=1)
# btn_gen_strat = gr.Button("✨ Générer Matrices IA", variant="primary", scale=1)

lines = content.splitlines()
idx_btn = -1
for i, line in enumerate(lines):
    if 'btn_load_context = gr.Button("📂 Charger Facts & Stratégie"' in line:
        idx_btn = i
        break

if idx_btn != -1:
    # Check indentation
    indent = lines[idx_btn][:lines[idx_btn].find('btn_load_context')]
    lines[idx_btn] = f'{indent}btn_load_context = gr.Button("📊 Charger Données Fin.", variant="secondary", scale=1)'
    lines.insert(idx_btn + 1, f'{indent}btn_gen_strat = gr.Button("✨ Générer Matrices IA", variant="primary", scale=1)')
else:
    print("Error locating button line via loop")


# 2. DEFINE NEW FUNCTION generate_strategy_only
# We will append it before `load_context_and_strategy` or after.
# Let's verify `load_context_and_strategy` location.
# It starts around line 319.

# We need to rewrite `load_context_and_strategy` to ONLY do financials.
# And add `generate_strategy_only`.

logic_code = """                # SPLIT LOGIC: 1. Financials, 2. Strategy

                # Helper to reload manager
                def _reload_manager():
                    import importlib
                    import facts_manager
                    importlib.reload(facts_manager)
                    return facts_manager.facts_manager

                def load_financials_only(ticker_ref):
                    print(f"DEBUG: Loading financials for {ticker_ref}...")
                    try:
                        mgr = _reload_manager()
                        if not ticker_ref:
                            raise ValueError("Ticker vide")
                        
                        mgr.ingest_financial_facts(ticker_ref)
                        
                        # Load Financials to populate inputs
                        tam_val = mgr.get_fact_value("tam_global_market", 0)
                        sam_val = mgr.get_fact_value("sam_percent", 20)
                        som_val = mgr.get_fact_value("som_share", 5)
                        
                        if sam_val < 1 and sam_val > 0: sam_val = sam_val * 100
                        if som_val < 1 and som_val > 0: som_val = som_val * 100
                        
                        return tam_val, sam_val, som_val
                    except Exception as e:
                         print(f"❌ Error Financials: {e}")
                         return 0, 0, 0

                def generate_strategy_matrices(ticker_ref, industry_context):
                    print(f"DEBUG: Generating Strategy Matrices for {ticker_ref} or {industry_context}...")
                    try:
                        mgr = _reload_manager()
                        
                        # Identifier: Ticker > Industry Context
                        target_name = ticker_ref if ticker_ref else industry_context
                        if not target_name:
                             target_name = "Acteur Générique"
                        
                        # Use ticker if available, otherwise None
                        tik = ticker_ref if ticker_ref else None
                        
                        print(f"🔄 Syncing strategy for {target_name}...")
                        mgr.ingest_strategic_facts(target_name, tik)
                        
                        # RELOAD VISUALIZATIONS
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

# We need to replace `def load_context_and_strategy(...)` with the above two functions.
# Locate start and end of `load_context_and_strategy`.
# Start: `def load_context_and_strategy(ticker_ref):`
# End: Just before `load_event = btn_load_context.click`

idx_def_start = -1
for i, line in enumerate(lines):
    if "def load_context_and_strategy(ticker_ref):" in line:
        idx_def_start = i
        break

idx_bindings = -1
for i, line in enumerate(lines):
    if "load_event = btn_load_context.click" in line:
        idx_bindings = i
        break

if idx_def_start == -1 or idx_bindings == -1:
    print("Could not find function bounds")
    exit(1)

# Remove the old function lines
# Be careful about `import traceback` line above the function
if "import traceback" in lines[idx_def_start-2]:
     idx_def_start -= 2

# Insert new logic
lines[idx_def_start:idx_bindings] = logic_code.splitlines() # Replace block

# 3. UPDATE BINDINGS
# Old:
#                 load_event = btn_load_context.click(
#                     load_context_and_strategy,
#                     inputs=[context_ticker],
#                     outputs=[plot_swot, plot_bcg, plot_pestel, tam_input, sam_pct_input, som_share_input]
#                 ).success( ... )

# New:
#                 # 1. Financials Button
#                 btn_load_context.click(
#                     load_financials_only,
#                     inputs=[context_ticker],
#                     outputs=[tam_input, sam_pct_input, som_share_input]
#                 ).success(refresh_market_sizing, ...)
#
#                 # 2. Strategy Button
#                 btn_gen_strat.click(
#                     generate_strategy_matrices,
#                     inputs=[context_ticker, input_industry], # Pass industry as fallback
#                     outputs=[plot_swot, plot_bcg, plot_pestel]
#                 )

new_bindings = """                # Bindings
                
                # 1. Financial Load (Linked to Calc)
                btn_load_context.click(
                    load_financials_only,
                    inputs=[context_ticker],
                    outputs=[tam_input, sam_pct_input, som_share_input]
                ).success(
                    refresh_market_sizing,
                    inputs=[scenario_radio, tam_input, sam_pct_input, som_share_input, context_ticker, input_industry, input_region, input_horizon, input_currency],
                    outputs=[plot_waterfall, plot_football, facts_display, sources_table]
                )

                # 2. Strategy Generation (Independent)
                btn_gen_strat.click(
                    generate_strategy_matrices,
                    inputs=[context_ticker, input_industry],
                    outputs=[plot_swot, plot_bcg, plot_pestel]
                )
"""

# We need to find where the old bindings ended.
# They started at `idx_bindings`.
# They ended before `def load_initial_state():` or empty lines.

idx_init_state = -1
for i in range(len(lines)): # re-scan because lines length changed
    if "def load_initial_state():" in lines[i]:
        idx_init_state = i
        break

# The bindings replace logic is safer if done by replacing the specific block found previously.
# But since we modified the list `lines` in step 2, indices shifted.
# We must re-locate bindings in the NEW `lines`.

# Find where we inserted logic code? No, we need to look for `load_event = btn_load_context.click` which we haven't removed yet.
# Actually, step 2 replaced `load_context_and_strategy` code BUT NOT the bindings because we stopped at `idx_bindings`.
# So `lines` now contains the old bindings starting at what was `idx_bindings`, but shifted?
# No, we replaced `lines[idx_def_start:idx_bindings]` with new code.
# So `lines[idx_def_start + len(logic_code_lines)]` is roughly where the bindings start now.

idx_bind_start = -1
for i, line in enumerate(lines):
    if "load_event = btn_load_context.click" in line:
        idx_bind_start = i
        break

idx_bind_end = -1
for i in range(idx_bind_start, len(lines)):
    if "def load_initial_state():" in lines[i]:
        idx_bind_end = i
        break
    # Or just look for empty lines or comments
    
# Actually `load_event` block spans multiple lines.
# And `.success(...)` too.
# It ends before `def load_initial_state():`.

if idx_bind_start != -1 and idx_bind_end != -1:
    # Replace bindings
    # Be careful to remove the old bindings completely.
    lines[idx_bind_start:idx_bind_end] = new_bindings.splitlines()

# WRITE BACK
with open(file_path, 'w') as f:
    f.write("\n".join(lines))

print("File updated with separated buttons.")
