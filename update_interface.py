
import os

file_path = "/Users/robincrifo/Documents/KPMG/kpmg/HACK-KPMG/kpmg_interface.py"

new_function_code = """
                # LOGIQUE MARKET SIZING
                def refresh_market_sizing(scenario, tam_val, sam_pct, som_pct, ticker_ref):
                    # 1. Update Temporary Facts from Inputs (Macro)
                    # We update the facts manager in memory so the engine sees the slider values
                    try:
                        facts_manager.facts_manager.add_or_update_fact({"key": "tam_global_market", "value": tam_val, "category": "market_estimation"})
                        facts_manager.facts_manager.add_or_update_fact({"key": "sam_percent", "value": sam_pct, "category": "market_estimation"})
                        facts_manager.facts_manager.add_or_update_fact({"key": "som_share", "value": som_pct, "category": "market_estimation"})
                    except:
                        pass # Handle potential reload issues gracefully

                    # 2. Run Engine
                    from market_estimation_engine import MarketEstimationEngine
                    engine = MarketEstimationEngine(facts_manager.facts_manager)
                    
                    estimations = engine.get_all_estimations()
                    
                    # 3. Generate HTML for 4 Components
                    html_content = "<div style='display: grid; grid_template_columns: repeat(2, 1fr); gap: 20px;'>"
                    
                    for comp in estimations:
                        # Format Value
                        val_display = "Données manquantes"
                        if comp.estimated_value is not None:
                            val_display = format_currency(comp.estimated_value)
                        
                        # Data Used List
                        data_list = ""
                        for d in comp.data_used:
                            d_val = "N/A"
                            if d.get("value") is not None:
                                d_val = f"{d['value']} {d.get('unit','')}"
                            
                            status_icon = "✅" if d.get("value") is not None else "⚠️"
                            data_list += f"<li style='font-size:0.9em; margin-bottom:4px;'>{status_icon} <b>{d.get('key')}</b>: {d_val}</li>"
                        
                        html_content += f\"\"\"
                        <div class="card-panel" style="border-top: 4px solid {comp.color} !important;">
                            <div style="display:flex; justify_content:space-between; align_items:center; margin-bottom:10px;">
                                <h3 style="margin:0; color:{comp.color}; font-size:1.1em;">{comp.name}</h3>
                                <div style="background:{comp.color}22; color:{comp.color}; padding:2px 8px; border-radius:10px; font-size:0.8em; font-weight:bold;">{comp.status.upper()}</div>
                            </div>
                            
                            <div style="text-align:center; margin: 15px 0;">
                                <div style="font-size:2em; font-weight:bold; color:white;">{val_display}</div>
                                <div style="font-size:0.9em; color:#90a4ae;">Confiance: {comp.confidence.upper()}</div>
                            </div>
                            
                            <div style="margin-bottom:12px;">
                                <div style="font-weight:600; font-size:0.9em; color:#E0E0E0; margin-bottom:4px;">Méthode</div>
                                <div style="font-size:0.85em; color:#B0BEC5; font-style:italic;">{comp.method_description}</div>
                            </div>
                            
                            <div style="background:rgba(255,255,255,0.03); padding:8px; border-radius:6px; margin-bottom:10px;">
                                <div style="font-weight:600; font-size:0.9em; color:#E0E0E0; margin-bottom:4px;">Données Clés</div>
                                <ul style="list-style:none; padding-left:0; margin:0; color:#B0BEC5;">
                                    {data_list}
                                </ul>
                            </div>
                            
                            <div style="font-size:0.85em; color:#90a4ae; border-left: 2px solid #546E7A; padding-left:8px;">
                                <span style="font-weight:600;">Palliation :</span> {comp.missing_data_strategy}
                            </div>
                        </div>
                        \"\"\"
                    
                    html_content += "</div>"
                    
                    # 4. Generate Visualizations (Keeping Waterfall/Football logic as visual aids)
                    # Macro Comp (Index 0)
                    macro_comp = estimations[0]
                    som_val = macro_comp.estimated_value if macro_comp.estimated_value else 0
                    
                    # Waterfall needs TAM/SAM/SOM breakdown. The macro comp computed the final SOM.
                    # We can re-derive the intermediates or assume the function inputs (tam_val etc) are the truth for the waterfall.
                    # Let's use inputs as they are "what-if" parameters.
                    calc_sam = tam_val * (sam_pct / 100) if tam_val else 0
                    calc_som = calc_sam * (som_pct / 100)
                    
                    if tam_val > 0:
                         fig_waterfall = analytics_viz.plot_market_sizing_waterfall(tam_val, calc_sam, calc_som)
                    else:
                         import plotly.graph_objects as go
                         fig_waterfall = go.Figure().add_annotation(text="Définissez le TAM pour voir le Waterfall", showarrow=False, font=dict(color="white"))
                         fig_waterfall.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

                    # Football Field - Use Engine Triangulation inputs
                    triang_comp = estimations[3] # Index 3 is Triangulation
                    ranges = []
                    # Add Macro
                    if estimations[0].estimated_value:
                        v = estimations[0].estimated_value
                        ranges.append({'label': 'Macro (Top-Down)', 'min': v*0.9, 'max': v*1.1, 'val': v})
                    # Add Demand
                    if estimations[1].estimated_value:
                        v = estimations[1].estimated_value
                        ranges.append({'label': 'Demande (Bottom-Up)', 'min': v*0.9, 'max': v*1.1, 'val': v})
                    # Add Supply
                    if estimations[2].estimated_value:
                        v = estimations[2].estimated_value
                        ranges.append({'label': 'Offre (Production)', 'min': v*0.9, 'max': v*1.1, 'val': v})
                    
                    if ranges:
                        fig_football = analytics_viz.plot_valuation_football_field(ranges)
                    else:
                        import plotly.graph_objects as go
                        fig_football = go.Figure().add_annotation(text="Pas assez de données pour triangulation", showarrow=False, font=dict(color="white"))
                        fig_football.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

                    return fig_waterfall, fig_football, html_content, ""
"""

def update_file():
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    start_idx = -1
    end_idx = -1
    
    # Locate the function definition and end
    for i, line in enumerate(lines):
        if "def refresh_market_sizing" in line:
            start_idx = i - 1 # Include comment above
            # Search for the next function def to identify end, or the indentation change
            continue
            
        if start_idx != -1 and "return fig_waterfall, fig_football" in line:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        print(f"Replacing lines {start_idx} to {end_idx}")
        
        # Keep lines before and after
        new_lines = lines[:start_idx] + [new_function_code] + lines[end_idx+1:]
        
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print("File updated successfully.")
    else:
        print("Could not find function bounds.")

if __name__ == "__main__":
    update_file()
