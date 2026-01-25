
import os

file_path = "/Users/robincrifo/Documents/KPMG/kpmg/HACK-KPMG/kpmg_interface.py"

# CONSTANTS
# We need to preserve imports if any.
# We will target the function definition block.

new_function_code = """                # LOGIQUE MARKET SIZING (UPDATED FOR GRANULARITY)
                def refresh_market_sizing(scenario, tam_val, sam_pct, som_pct, ticker_ref, industry, region, horizon, currency):
                    # Construct Scope String dynamically
                    scope_str = f"{industry} en {region} (Horizon {horizon}) - {currency}"
                    facts_manager.facts_manager.set_market_scope(scope_str)

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
                    
                    # 3. Generate HTML for 4 Components
                    
                    # HERO INSIGHT (CB INSIGHTS STYLE)
                    hero_val = "N/A"
                    if best_comp.estimated_value:
                        hero_val = format_currency(best_comp.estimated_value)
                        
                    # Confidence Color
                    conf_color = "#4CAF50" # Green for High
                    if best_comp.confidence == "medium": conf_color = "#FF9800"
                    if best_comp.confidence == "low": conf_color = "#F44336"
                    
                    decision_html = f'''
                    <div style="background: linear_gradient(135deg, #1A237E 0%, #0D47A1 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); text-align: center; border: 1px solid rgba(255,255,255,0.1);">
                        
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
                    
                    <h3 style="margin-bottom: 20px; color: #E0E0E0; border-left: 4px solid #BBDEFB; padding-left: 10px;">🔍 Analyse Méthodologique Détaillée</h3>
                    '''
                    
                    html_content = decision_html + "<div style='display: grid; grid_template_columns: repeat(2, 1fr); gap: 20px;'>"
                    
                    for comp in estimations:
                        is_active = (comp.id == best_comp.id)
                        
                        # Style variations based on Active status
                        opacity = "1.0" if is_active else "0.6"
                        filter_style = "" if is_active else "filter: grayscale(80%);"
                        border_style = f"4px solid {comp.color}" if is_active else "1px solid #444"
                        
                        scale_transform = "transform: scale(1.02);" if is_active else ""
                        box_shadow = f"box-shadow: 0 4px 15px {comp.color}40;" if is_active else ""
                        
                        badge_html = ""
                        if is_active:
                            badge_html = f'<div style="background:{comp.color}; color:black; padding:2px 8px; border-radius:10px; font-size:0.8em; font-weight:bold; margin-left:10px;">✅ RETENU</div>'
                        else:
                            badge_html = f'<div style="border:1px solid #666; color:#888; padding:2px 8px; border-radius:10px; font-size:0.8em; margin-left:10px;">ÉCARTÉ</div>'

                        # Format Value
                        val_display = "Données manquantes"
                        if comp.estimated_value is not None:
                            val_display = format_currency(comp.estimated_value)
                        
                        # Data Used List with Type Badge
                        data_list = ""
                        for d in comp.data_used:
                            d_val = "N/A"
                            if d.get("value") is not None:
                                d_val = f"{d['value']} {d.get('unit','')}"
                                if isinstance(d['value'], (int, float)) and d['value'] > 1000:
                                    d_val = f"{d['value']:,.0f} {d.get('unit','')}"
                            
                            status_icon = "✅" if d.get("value") is not None else "⚠️"
                            
                            # Source Type Badge
                            src_type = d.get("source_type", "Standard")
                            type_badge_color = "#666"
                            if src_type in ["Proxy", "Estimation", "Interne"]: type_badge_color = "#FF9800"
                            if src_type == "Manquant": type_badge_color = "#F44336"
                            
                            type_badge = f'<span style="background:{type_badge_color}; color:white; font-size:0.7em; padding:1px 4px; border-radius:4px; margin-left:5px;">{src_type}</span>'
                            
                            data_list += f"<li style='font-size:0.9em; margin-bottom:4px;'>{status_icon} <b>{d.get('key')}</b> {type_badge}: {d_val}</li>"
                        
                        # Calculation Breakdown
                        breakdown_html = ""
                        if comp.calculation_breakdown:
                             breakdown_html = f'''
                             <div style="margin-top:10px; padding:10px; background:rgba(0,0,0,0.3); border-radius:6px; border-left: 2px solid {comp.color};">
                                <div style="font-size:0.75em; color:{comp.color}; text-transform:uppercase; margin-bottom:4px;">Stratégie: {comp.selected_strategy_name}</div>
                                <div style="font-family:monospace; font-size:0.9em; color:#FFF;">{comp.calculation_breakdown}</div>
                             </div>
                             '''

                        html_content += f'''
                        <div class="card-panel" style="border-top: {border_style} !important; opacity: {opacity}; {filter_style} {scale_transform} {box_shadow} transition: all 0.3s ease;">
                            <div style="display:flex; justify-content:space-between; align_items:center; margin-bottom:10px;">
                                <div style="display:flex; align_items:center;">
                                    <h3 style="margin:0; color:{comp.color}; font-size:1.1em;">{comp.name}</h3>
                                    {badge_html}
                                </div>
                                <div style="background:{comp.color}22; color:{comp.color}; padding:2px 8px; border-radius:10px; font-size:0.8em; font-weight:bold;">{comp.status.upper()}</div>
                            </div>
                            
                            <div style="text-align:center; margin: 15px 0;">
                                <div style="font-size:2em; font-weight:bold; color:white;">{val_display}</div>
                                <div style="font-size:0.9em; color:#90a4ae;">Confiance: {comp.confidence.upper()}</div>
                            </div>
                            
                            {breakdown_html}
                            
                            <div style="margin-top:15px; border-top:1px solid #444; padding-top:10px;">
                                <div style="font-weight:600; font-size:0.9em; color:#E0E0E0; margin-bottom:8px;">Données utilisées & Sources</div>
                                <ul style="list-style-type:none; padding-left:0; color:#B0BEC5;">
                                    {data_list}
                                </ul>
                            </div>
                            
                            <div style="font-size:0.85em; color:#ffcc80; font-style:italic; margin-top:10px;">
                                {comp.missing_data_strategy if comp.status != "complete" else ""}
                            </div>
                        </div>
                        '''
                        
                    html_content += "</div>"
                    
                    return html_content, sources_df
"""

with open(file_path, 'r') as f:
    content = f.read()

# Naive find and replace might fail if indentation or spacing differs slightly.
# We will identify the start and end of the function manually via markers.

start_marker = "# LOGIQUE MARKET SIZING"
end_marker = "# Helper to export" # Assuming this comes after? Or we can just find the end of indentation.

# Actually, in the file `kpmg_interface.py`, the logical end of the file is near.
# Let's see the context from previous reads.
# The file ends with `if __name__ == "__main__":` block usually?
# Or just ends.

# Let's try to find lines 152 to the end of the indentation block.
# Previous view showed:
# 152:                 def refresh_market_sizing(scenario, tam_val, sam_pct, som_pct, ticker_ref, industry, region, horizon, currency):
# ...
# And it returns html_content, sources_df at the end.

# Safest way: Load lines, find start line, find end line (where indentation drops back to column 16 or less).

lines = content.splitlines()
start_index = -1
for i, line in enumerate(lines):
    if "def refresh_market_sizing" in line:
        start_index = i
        break

if start_index == -1:
    print("Could not find function definition")
    exit(1)

# Find end index (dedent)
end_index = len(lines)
current_indent = len(lines[start_index]) - len(lines[start_index].lstrip())

for i in range(start_index + 1, len(lines)):
    if len(lines[i].strip()) > 0: # Skip empty lines
        indent = len(lines[i]) - len(lines[i].lstrip())
        if indent <= current_indent: # Dedent detected (but need to check if it's not just a closing bracket on same level? No, python defs usually dedent completely)
             # Wait, the function is inside a `with gr.Blocks`? or `launch_dashboard`?
             # It is indented.
             # The next block might be `return app`.
             # If I encounter a line with SAME or LESS indentation than the def, the function is over.
             if indent <= current_indent:
                end_index = i
                break

print(f"Replacing lines {start_index} to {end_index}")

# Construct new content
new_lines = new_function_code.splitlines() # These are already indented?
# The code string I wrote above is indented with 16 spaces (assuming it's inside the function).
# Wait, I indented the string content in variable `new_function_code`.
# But `kpmg_interface.py` indentation level is likely 4 or 8 or 12 or 16.
# Let's check the view_file output again.
# Line 152 in view was: `                def refresh_market_sizing...`
# That looks like 16 spaces.

# My string has variable indentation.
# I should probably just write the file using `replace_file_content` if I knew the exact range, but `run_command` via script is what I chose.
# I will use the indentation from the file to adjust if needed, but python string literal indentation is tricky.

# Let's just output the new file content.
final_lines = lines[:start_index-1] # Keep the '# LOGIQUE MARKET SIZING' comment which is line 151 in my view? 
# View said:
# 151:                 # LOGIQUE MARKET SIZING (UPDATED FOR CB INSIGHTS)
# 152:                 def refresh_market_sizing...
# So I should start replacement at start_index-1 to replace the comment too.

final_lines = lines[:start_index-1] + new_lines + lines[end_index:]

with open(file_path, 'w') as f:
    f.write("\n".join(final_lines))

print("File updated successfully.")
