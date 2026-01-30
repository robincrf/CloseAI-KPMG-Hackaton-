
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
    
    # Sober Consulting Theme
    theme = gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        body_background_fill="#0F172A",
        block_background_fill="#1E293B",
        block_border_width="1px",
        block_border_color="#334155",
        block_label_text_color="#94A3B8",
        input_background_fill="#0F172A",
        button_primary_background_fill="#334155", 
        button_primary_text_color="#F8FAFC",
        button_secondary_background_fill="#0F172A",
        slider_color="#64748B"
    )

    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    body, gradio-app { font-family: 'Inter', sans-serif !important; background-color: #0F172A; }
    .header-container {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1.5rem; background: linear-gradient(90deg, #00338D 0%, #001E55 100%);
        border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0, 51, 141, 0.3);
    }
    .header-title { color: white; font-size: 1.8rem; font-weight: 700; }
    .header-subtitle { color: #0091DA; font-size: 1rem; font-weight: 500; }
    
    details.fact-details { background: transparent; border: 1px solid #334155; border-radius: 6px; margin-bottom: 8px; }
    summary.fact-summary { padding: 10px 15px; cursor: pointer; color: #E2E8F0; font-weight: 500; list-style: none; display: flex; justify-content: space-between; }
    summary.fact-summary::-webkit-details-marker { display: none; }
    .fact-content { padding: 15px; border-top: 1px solid #334155; color: #CBD5E1; font-size: 0.9em; }
    
    .segment-card, .actor-card, .gap-card, .axis-card { background: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 15px; transition: border-color 0.2s; }
    .segment-card:hover, .actor-card:hover { border-color: #64748B; }
    .segment-grid, .actor-grid, .gap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 15px; margin-top: 15px; }
    
    .card-badge, .source-badge { font-size: 0.75em; padding: 1px 6px; border-radius: 4px; border: 1px solid #475569; color: #94A3B8; text-transform: uppercase; }
    .typology-leader { color: #4ADE80; font-weight: 600; }
    .typology-challenger { color: #60A5FA; font-weight: 600; }
    .typology-niche { color: #A3A3A3; font-weight: 600; }
    
    .offerings-matrix { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .offerings-matrix th { text-align: center; color: #94A3B8; padding: 8px; font-weight: 500; border-bottom: 1px solid #334155; }
    .offerings-matrix td { text-align: center; padding: 8px; border-bottom: 1px solid #1E293B; color: #E2E8F0; }
    .feat-confirmed { color: #4ADE80; }
    .feat-declared { color: #FBBF24; }
    .feat-absent { color: #EF4444; opacity: 0.5; }
    
    .gap-met { border-left: 3px solid #4ADE80; }
    .gap-partial { border-left: 3px solid #FBBF24; }
    .gap-unmet { border-left: 3px solid #EF4444; }
    
    .source-list { display: flex; flex-direction: column; gap: 8px; }
    .source-item { padding: 10px; border-bottom: 1px solid #334155; }
    
    .check-list { display: flex; flex-direction: column; gap: 5px; }
    .check-item { display: flex; justify-content: space-between; padding: 8px; border-radius: 4px; }
    .check-item.ok { color: #4ADE80; }
    .check-item.warn { color: #FBBF24; }
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
        
        # ═══════════════════════════════════════════════════════════════════════
        # GLOBAL CONTEXT STATES - Shared between tabs
        # ═══════════════════════════════════════════════════════════════════════
        state_company = gr.State(value="")
        state_country = gr.State(value="France")
        state_year = gr.State(value="2025")
        state_context = gr.State(value="")  # Additional context / offerings
        state_sizing_summary = gr.State(value="")  # Summary for downstream modules
        state_seg_summary = gr.State(value="")  # Segmentation summary for Competitive Analysis
        
        with gr.Tabs():
            
            # ─── ONGLET 1 : ASSISTANT (FIRST TAB) ───
            with gr.Tab("Assistant"):
                gr.Markdown("### Assistant méthodologique")
                gr.Markdown("""
                **Bienvenue dans KPMG Market Sizer.**
                
                Je suis votre assistant dédié à l'analyse stratégique. Je peux vous aider à :
                - Comprendre la méthodologie d'estimation de marché
                - Expliquer les sources et hypothèses utilisées
                - Interpréter les résultats de segmentation ou d'analyse concurrentielle
                
                *Posez-moi vos questions ci-dessous.*
                """)
                with gr.Row():
                    with gr.Column():
                        gr.ChatInterface(
                            fn=rag_stream_function,
                            chatbot=gr.Chatbot(
                                value=[{"role": "assistant", "content": "Bonjour consultant KPMG ! 👋 Avez-vous une question sur un marché ? une entreprise ?"}],
                                height=500
                            )
                        )
            
            # ─── ONGLET 2 : MARKET SIZING ───
            with gr.Tab("Taille de marché"):
                
                # SECTION 1: PARAMÈTRES
                gr.Markdown("### Paramètres de l'analyse")
                
                with gr.Row():
                    ctx_company = gr.Textbox(
                        label="Entreprise Cible",
                        placeholder="ex: Doctolib, Alan, Qonto...",
                        value=""
                    )
                    ctx_country = gr.Dropdown(
                        choices=["France", "Allemagne", "Pologne", "Espagne", "Italie", "Royaume-Uni", "États-Unis", "Brésil", "Japon"],
                        label="Pays / Zone",
                        value="France",
                        allow_custom_value=True
                    )
                    ctx_year = gr.Dropdown(
                        choices=["2024", "2025", "2026", "2027", "2028"],
                        label="Année",
                        value="2025",
                        allow_custom_value=True
                    )
                
                with gr.Row():
                    ctx_additional = gr.Textbox(
                        label="Contexte Additionnel",
                        placeholder="Précisions sur l'offre, le modèle économique ou le secteur...",
                        lines=1,
                        value="",
                        scale=3
                    )
                    
                    btn_run_sizing = gr.Button("Calculer l'estimation", variant="primary", scale=1)
                
                # RÉSULTAT (AFFICHÉ EN HAUT)
                gr.Markdown("### Résultat de l'Estimation")
                with gr.Row():
                    with gr.Column(scale=2):
                        out_final_result = gr.HTML()
                    with gr.Column(scale=1):
                        out_reliability = gr.HTML()
                
                # SECTION 2: CONTEXTE VERROUILLÉ
                with gr.Accordion("1. Contexte verrouillé", open=True):
                    out_context_lock = gr.HTML()
                
                # SECTION 3: DÉFINITION DU MARCHÉ
                with gr.Accordion("2. Définition du marché", open=True):
                    out_market_definition = gr.HTML()
                
                # SECTION 4: FACTS UTILISÉS (REMPLACEMENT UX)
                with gr.Accordion("3. Facts Locaux Mobilisés", open=True):
                    # REMPLACÉ: gr.Dataframe
                    out_facts_registry = gr.HTML(label="Registre des Facts")
                
                # SECTION 5: RECONSTRUCTION BOTTOM-UP
                with gr.Accordion("4. Reconstruction Bottom-Up Locale", open=True):
                    with gr.Row():
                        with gr.Column():
                            out_economic_unit = gr.HTML(label="Unité Économique")
                        with gr.Column():
                            out_addressable_pop = gr.HTML(label="Population Adressable")
                    with gr.Row():
                        with gr.Column():
                            out_unit_value = gr.HTML(label="Valeur Unitaire Locale")
                        with gr.Column():
                            out_adoption_rate = gr.HTML(label="Taux d'Adoption")
                
                # SECTION 6: CALCUL
                with gr.Accordion("5. Calcul Explicite", open=True):
                    out_calculation = gr.HTML()
                
                # SECTION 6b: HYPOTHÈSES DÉTAILLÉES (NEW)
                with gr.Accordion("5b. Hypothèses Quantifiées", open=True):
                    out_hypotheses_detailed = gr.HTML(label="Détail des Hypothèses avec Benchmarks")
                
                # SECTION 6c: ANALYSE DE SENSIBILITÉ (NEW)
                with gr.Accordion("5c. Analyse de Sensibilité", open=True):
                    out_sensitivity_analysis = gr.HTML(label="Scénarios et Impact des Variables")
                
                # SECTION 6d: IMPACT RÉGLEMENTAIRE (NEW)
                with gr.Accordion("5d. Impact Réglementaire", open=True):
                    out_regulatory_impact = gr.HTML(label="Lien Régulation → Hypothèses")
                
                # SECTION 6e: JUSTIFICATION DU PÉRIMÈTRE (NEW)
                with gr.Accordion("5e. Justification du Périmètre", open=True):
                    out_scope_analysis = gr.HTML(label="Périmètre et Alternatives")
                
                # SECTION 7: VALIDATION (REMPLACEMENT UX)
                with gr.Accordion("6. Contrôle de cohérence", open=True):
                    # REMPLACÉ: gr.Dataframe
                    out_validation_checklist = gr.HTML(label="Checklist de Cohérence")
                

                
                # SECTION 9: SOURCES (REMPLACEMENT UX)
                with gr.Accordion("7. Registre des Sources", open=False):
                    # REMPLACÉ: gr.Dataframe
                    out_sources_list = gr.HTML(label="Sources & Traçabilité")
                
                # HANDLER
                def run_contextual_sizing(company, country, year, additional):
                    if not company.strip():
                        return (
                            "<div style='color:#FF5252; padding:20px;'>Veuillez entrer un nom d'entreprise.</div>",
                            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                            "", "France", "2025", "", ""  # States unchanged on error
                        )
                    
                    from strategic_facts_service import strategic_facts_service
                    result = strategic_facts_service.generate_contextual_market_sizing(
                        company_name=company.strip(),
                        country=country.strip(),
                        year=year.strip(),
                        additional_context=additional.strip()
                    )
                    
                    if not result.get("success"):
                        error_msg = result.get("error", "Erreur inconnue")
                        return (
                            f"<div style='color:#FF5252; padding:20px;'>Erreur : {error_msg}</div>",
                            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                            "", "France", "2025", "", ""  # States unchanged on error
                        )
                    
                    analysis = result.get("analysis", {})
                    
                    # 1. CONTEXT LOCK
                    ctx = analysis.get("context_lock", {})
                    ctx_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 4px solid #0091DA;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div><span style="opacity: 0.7;">Entreprise:</span> <b style="color: #0091DA;">{ctx.get('company', 'N/A')}</b></div>
                            <div><span style="opacity: 0.7;">Pays:</span> <b>{country}</b></div>
                            <div><span style="opacity: 0.7;">Année:</span> <b>{year}</b></div>
                            <div><span style="opacity: 0.7;">Modèle Local:</span> <b>{ctx.get('local_business_model', 'N/A')[:50]}...</b></div>
                        </div>
                        <div style="margin-top: 10px;"><span style="opacity: 0.7;">Offres pertinentes:</span> {', '.join(ctx.get('company_offerings', []))}</div>
                        {"<div style='color: #FFAB00; margin-top: 10px;'>Infos manquantes: " + ', '.join(ctx.get('missing_info', [])) + "</div>" if ctx.get('missing_info') else ""}
                    </div>
                    """
                    
                    # 2. MARKET DEFINITION
                    mkt = analysis.get("market_definition", {})
                    local_adapt = mkt.get("local_adaptations", {})
                    excluded = mkt.get("excluded_segments", [])
                    
                    mkt_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="font-weight: bold; color: #0091DA; font-size: 1.1em; margin-bottom: 10px;">{mkt.get('market_name', 'N/A')}</div>
                        <div style="font-style: italic; margin-bottom: 15px; opacity: 0.9;">{mkt.get('market_justification', 'N/A')}</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 5px;">
                                <div style="opacity: 0.7; font-size: 0.8em;">Maturité</div>
                                <div style="font-weight: bold;">{local_adapt.get('maturity_level', 'N/A').upper()}</div>
                            </div>
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 5px;">
                                <div style="opacity: 0.7; font-size: 0.8em;">Régulation</div>
                                <div style="font-weight: bold;">{local_adapt.get('regulatory_context', 'N/A')[:30]}...</div>
                            </div>
                        </div>
                        <div style="color: #FF5252; font-size: 0.9em;">
                            <b>Segments exclus:</b> {', '.join([e.get('segment', '') for e in excluded]) if excluded else 'Aucun'}
                        </div>
                    </div>
                    """
                    
                    # 3. FACTS HTML
                    facts_data = analysis.get("facts_used", [])
                    facts_html = "<div class='source-list'>"
                    for f in facts_data:
                        # Determine badge style
                        src_type = f.get("source_type", "N/A").lower()
                        badge_class = "primary" if "primary" in src_type or "report" in src_type else "secondary"
                        
                        facts_html += f"""
                        <div class="source-item">
                            <div class="source-header">
                                <span class="source-badge {badge_class}">{f.get('source_type', 'Autre').upper()}</span>
                                <span>Confiance: <b style="color:{'#00C853' if f.get('confidence')=='high' else '#FFAB00'}">{f.get('confidence', 'medium').upper()}</b></span>
                            </div>
                            <div style="font-weight: bold; margin: 4px 0; color: #E0E0E0;">{f.get('key', 'Fact').replace('_', ' ').capitalize()}</div>
                            <div style="font-size: 1.1em; color: white;">{f.get('value', 'N/A')} <span style="font-size:0.8em; opacity:0.7">{f.get('unit', '')}</span></div>
                            <div style="font-size: 0.85em; opacity: 0.7; margin-top: 5px;"><i>Source: {f.get('source', 'Inconnue')}</i></div>
                            <div style="font-size: 0.8em; color: #B0B0B0; margin-top: 2px;">{f.get('notes', '')}</div>
                        </div>
                        """
                    facts_html += "</div>"
                    
                    # 4. BOTTOM-UP COMPONENTS
                    bu = analysis.get("bottom_up_reconstruction", {})
                    
                    # Economic Unit
                    eu = bu.get("economic_unit", {})
                    eu_html = f"""
                    <div style="background: rgba(0,145,218,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #0091DA;">
                        <div style="font-weight: bold; margin-bottom: 5px;">{eu.get('name', 'N/A')}</div>
                        <div style="font-size: 0.9em; opacity: 0.8;">{eu.get('definition', 'N/A')}</div>
                        <div style="font-size: 0.8em; color: #0091DA; margin-top: 5px;">Pertinence: {eu.get('relevance', 'N/A')}</div>
                    </div>
                    """
                    
                    # Addressable Population
                    ap = bu.get("addressable_population", {})
                    filters = ap.get("filters_applied", [])
                    filters_html = "".join([f"<div style='padding: 5px; background: rgba(0,0,0,0.2); margin: 3px 0; border-radius: 4px; display: flex; justify-content: space-between;'><span>{f.get('filter_name', '')}: {f.get('filter_value', '')}</span><span style='color: #0091DA;'>→ {f.get('remaining_units', 'N/A'):,}</span></div>" for f in filters])
                    
                    ap_html = f"""
                    <div style="background: rgba(0,200,83,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #00C853;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Total dans le pays:</span>
                            <span style="font-weight: bold;">{ap.get('total_units_in_country', 'N/A'):,}</span>
                        </div>
                        <div style="font-size: 0.9em;">{filters_html}</div>
                        <div style="margin-top: 10px; padding: 10px; background: #00C853; color: white; border-radius: 5px; text-align: center;">
                            <div style="font-size: 0.8em;">UNITÉS ÉLIGIBLES</div>
                            <div style="font-size: 1.5em; font-weight: bold;">{ap.get('final_addressable_units', 'N/A'):,}</div>
                        </div>
                    </div>
                    """
                    
                    # Unit Value
                    uv = bu.get("local_unit_value", {})
                    uv_html = f"""
                    <div style="background: rgba(255,171,0,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #FFAB00;">
                        <div style="font-size: 1.5em; font-weight: bold; color: #FFAB00;">{uv.get('annual_price_local', 'N/A'):,} {uv.get('currency', 'EUR')}</div>
                        <div style="font-size: 0.9em; margin-top: 5px;">{uv.get('comparison_vs_reference', 'N/A')}</div>
                        <div style="font-size: 0.8em; opacity: 0.7; margin-top: 5px;">Ajustement: {uv.get('adjustment_rationale', 'N/A')}</div>
                    </div>
                    """
                    
                    # Adoption Rate
                    ar = bu.get("adoption_rate", {})
                    ar_html = f"""
                    <div style="background: rgba(98,0,234,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #6200EA;">
                        <div style="font-size: 1.5em; font-weight: bold; color: #6200EA;">{ar.get('estimated_rate_percent', 'N/A')}%</div>
                        <div style="font-size: 0.9em; margin-top: 5px;">{ar.get('rate_justification', 'N/A')}</div>
                        <div style="font-size: 0.8em; opacity: 0.7; margin-top: 5px;">Source: {ar.get('rate_source', 'N/A')}</div>
                    </div>
                    """
                    
                    # 5. CALCULATION
                    calc = analysis.get("calculation", {})
                    steps = calc.get("step_by_step", [])
                    final_est = calc.get("final_estimate", {})
                    
                    calc_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="font-family: monospace; background: #121212; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <div style="color: #0091DA; margin-bottom: 10px;"># {calc.get('formula', 'N/A')}</div>
                            {"".join([f"<div style='padding: 5px 0; border-bottom: 1px solid #333;'>{step}</div>" for step in steps])}
                        </div>
                    </div>
                    """
                    
                    # 5b. HYPOTHESES DETAILED (NEW)
                    hypotheses = analysis.get("hypotheses_detailed", [])
                    hyp_html = "<div style='display: grid; gap: 15px;'>"
                    for hyp in hypotheses:
                        benchmarks = hyp.get("benchmark_references", [])
                        bench_html = ""
                        if benchmarks:
                            bench_html = "<div style='display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px;'>"
                            for b in benchmarks:
                                bench_html += f"<span style='background: rgba(0,145,218,0.2); padding: 3px 8px; border-radius: 4px; font-size: 0.75em;'>{b.get('country', 'N/A')}: {b.get('value', 'N/A')}% ({b.get('year', '')})</span>"
                            bench_html += "</div>"
                        
                        conf_range = hyp.get("confidence_range", {})
                        range_html = f"[{conf_range.get('low', 'N/A')} - {conf_range.get('central', 'N/A')} - {conf_range.get('high', 'N/A')}]" if conf_range else ""
                        
                        hyp_html += f"""
                        <div style="background: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 3px solid #6200EA;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <div style="font-weight: bold; color: #F8FAFC;">{hyp.get('variable', 'N/A').replace('_', ' ').title()}</div>
                                <span style="background: #6200EA; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.8em;">{hyp.get('central_value', 'N/A')} {hyp.get('unit', '')}</span>
                            </div>
                            <div style="font-size: 0.85em; color: #CBD5E1; margin-bottom: 8px;">{hyp.get('economic_rationale', 'N/A')}</div>
                            <div style="font-size: 0.8em; opacity: 0.7;">Intervalle de confiance: {range_html}</div>
                            {bench_html}
                            <div style="font-size: 0.75em; color: #FFAB00; margin-top: 8px;">Sensibilité: {hyp.get('sensitivity_impact', 'N/A')}</div>
                        </div>
                        """
                    if not hypotheses:
                        hyp_html += "<div style='opacity: 0.5;'>Aucune hypothèse détaillée disponible.</div>"
                    hyp_html += "</div>"
                    
                    # 5c. SENSITIVITY ANALYSIS (NEW)
                    sensitivity = analysis.get("sensitivity_analysis", {})
                    scenarios = sensitivity.get("scenarios", [])
                    sensitivities = sensitivity.get("key_sensitivities", [])
                    
                    sens_html = "<div>"
                    
                    # Scenarios Table
                    if scenarios:
                        sens_html += "<div style='margin-bottom: 20px;'>"
                        sens_html += "<div style='font-weight: bold; margin-bottom: 10px; color: #94A3B8;'>Scénarios</div>"
                        sens_html += "<table style='width: 100%; border-collapse: collapse; font-size: 0.85em;'>"
                        sens_html += "<thead><tr style='background: #1E293B;'>"
                        sens_html += "<th style='padding: 10px; text-align: left;'>Scénario</th>"
                        sens_html += "<th style='padding: 10px; text-align: center;'>Adoption</th>"
                        sens_html += "<th style='padding: 10px; text-align: center;'>Prix</th>"
                        sens_html += "<th style='padding: 10px; text-align: right; font-weight: bold;'>Résultat</th>"
                        sens_html += "</tr></thead><tbody>"
                        
                        scenario_colors = {"Conservateur": "#4ADE80", "Central": "#0091DA", "Optimiste": "#FFAB00"}
                        for sc in scenarios:
                            color = scenario_colors.get(sc.get('name', ''), '#9E9E9E')
                            result_val = sc.get('result', 0)
                            result_fmt = f"€{result_val/1e6:.1f}M" if result_val >= 1e6 else f"€{result_val:,.0f}"
                            sens_html += f"""
                            <tr style='border-bottom: 1px solid #334155;'>
                                <td style='padding: 10px;'><span style='color: {color}; font-weight: bold;'>{sc.get('name', 'N/A')}</span><br><span style='font-size: 0.8em; opacity: 0.7;'>{sc.get('description', '')[:50]}...</span></td>
                                <td style='padding: 10px; text-align: center;'>{sc.get('adoption_rate', 'N/A')}%</td>
                                <td style='padding: 10px; text-align: center;'>€{sc.get('price', 0):,}</td>
                                <td style='padding: 10px; text-align: right; font-weight: bold; color: {color};'>{result_fmt}</td>
                            </tr>
                            """
                        sens_html += "</tbody></table></div>"
                    
                    # Key Sensitivities
                    if sensitivities:
                        sens_html += "<div style='font-weight: bold; margin-bottom: 10px; color: #94A3B8;'>Impact des Variables Clés</div>"
                        sens_html += "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;'>"
                        for s in sensitivities:
                            impact_color = "#4ADE80" if '+' in str(s.get('impact_percent', '')) else "#F87171"
                            sens_html += f"""
                            <div style='background: #1E293B; padding: 12px; border-radius: 8px;'>
                                <div style='font-size: 0.8em; opacity: 0.7;'>{s.get('variable', 'N/A').replace('_', ' ').title()}</div>
                                <div style='font-size: 0.85em; margin: 5px 0;'>{s.get('delta', 'N/A')}</div>
                                <div style='color: {impact_color}; font-weight: bold;'>{s.get('impact_percent', 'N/A')}</div>
                            </div>
                            """
                        sens_html += "</div>"
                    
                    sens_html += f"<div style='margin-top: 15px; font-style: italic; opacity: 0.8; font-size: 0.85em;'>{sensitivity.get('sensitivity_conclusion', '')}</div>"
                    sens_html += "</div>"
                    
                    # 5d. REGULATORY IMPACT (NEW)
                    regulatory = analysis.get("regulatory_impact", {})
                    regulations = regulatory.get("key_regulations", [])
                    reg_links = regulatory.get("regulation_hypothesis_links", [])
                    
                    reg_html = "<div style='display: grid; gap: 15px;'>"
                    for reg in regulations:
                        impact_color = "#4ADE80" if reg.get('impact_direction') == 'positive' else "#F87171"
                        reg_html += f"""
                        <div style='background: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 3px solid {impact_color};'>
                            <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                <div style='font-weight: bold; color: #F8FAFC;'>{reg.get('regulation_name', 'N/A')}</div>
                                <span style='background: {impact_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75em;'>{reg.get('status', 'N/A').upper()}</span>
                            </div>
                            <div style='font-size: 0.85em; color: #CBD5E1; margin-bottom: 8px;'>{reg.get('description', 'N/A')}</div>
                            <div style='display: flex; gap: 15px; font-size: 0.8em;'>
                                <span style='opacity: 0.7;'>Organe: {reg.get('regulatory_body', 'N/A')}</span>
                                <span style='opacity: 0.7;'>Impact: {reg.get('impact_on', 'N/A').replace('_', ' ')}</span>
                            </div>
                            <div style='margin-top: 10px; padding: 8px; background: rgba(0,145,218,0.1); border-radius: 4px; font-size: 0.85em;'>
                                <b>Quantification:</b> {reg.get('quantification', 'N/A')}
                            </div>
                            <div style='font-size: 0.75em; opacity: 0.6; margin-top: 5px;'>Source: {reg.get('source', 'N/A')}</div>
                        </div>
                        """
                    
                    # Regulation-Hypothesis Links
                    if reg_links:
                        reg_html += "<div style='background: rgba(255,171,0,0.1); padding: 12px; border-radius: 8px; margin-top: 10px;'>"
                        reg_html += "<div style='font-weight: bold; color: #FFAB00; margin-bottom: 8px;'>Liens Régulation → Hypothèses</div>"
                        for link in reg_links:
                            reg_html += f"<div style='font-size: 0.85em; margin-bottom: 5px;'>• <b>{link.get('regulation_id', 'N/A')}</b> → <b>{link.get('hypothesis_id', 'N/A')}</b>: {link.get('link_explanation', 'N/A')}</div>"
                        reg_html += "</div>"
                    
                    if regulatory.get('regulatory_uncertainty'):
                        reg_html += f"<div style='font-size: 0.85em; color: #FFAB00; margin-top: 10px;'>Incertitude: {regulatory.get('regulatory_uncertainty', '')}</div>"
                    
                    if not regulations:
                        reg_html += "<div style='opacity: 0.5;'>Aucun impact réglementaire documenté.</div>"
                    reg_html += "</div>"
                    
                    # 5e. SCOPE ANALYSIS (NEW)
                    scope = analysis.get("scope_analysis", {})
                    alternatives = scope.get("alternatives_considered", [])
                    expansion = scope.get("expansion_potential", {})
                    
                    stance_colors = {"conservative": "#4ADE80", "balanced": "#0091DA", "expansive": "#FFAB00"}
                    stance = scope.get("scope_stance", "conservative")
                    stance_color = stance_colors.get(stance, "#9E9E9E")
                    stance_label = {"conservative": "Conservateur", "balanced": "Équilibré", "expansive": "Expansif"}.get(stance, stance)
                    
                    scope_html = f"""
                    <div style='background: #1E1E1E; padding: 20px; border-radius: 10px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                            <div style='font-size: 1.1em; font-weight: bold;'>{scope.get('chosen_scope', 'N/A')}</div>
                            <span style='background: {stance_color}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em;'>{stance_label.upper()}</span>
                        </div>
                        <div style='font-size: 0.9em; color: #CBD5E1; margin-bottom: 15px;'>{scope.get('scope_rationale', 'N/A')}</div>
                    """
                    
                    if alternatives:
                        scope_html += "<div style='font-weight: bold; margin-bottom: 10px; color: #94A3B8;'>Alternatives Non Retenues</div>"
                        scope_html += "<div style='display: grid; gap: 10px;'>"
                        for alt in alternatives:
                            conf_color = {"HIGH": "#4ADE80", "MEDIUM": "#FFAB00", "LOW": "#F87171", "VERY LOW": "#9E9E9E"}.get(alt.get('confidence', 'LOW'), '#9E9E9E')
                            val = alt.get('additional_value_estimate', 0)
                            val_fmt = f"+€{val/1e6:.1f}M" if val >= 1e6 else f"+€{val:,.0f}"
                            scope_html += f"""
                            <div style='background: #1E293B; padding: 12px; border-radius: 6px;'>
                                <div style='display: flex; justify-content: space-between;'>
                                    <div style='font-weight: bold; font-size: 0.9em;'>{alt.get('scope', 'N/A')}</div>
                                    <div><span style='color: {conf_color};'>{val_fmt}</span> <span style='opacity: 0.5; font-size: 0.75em;'>({alt.get('confidence', 'N/A')})</span></div>
                                </div>
                                <div style='font-size: 0.8em; opacity: 0.7; margin-top: 5px;'>{alt.get('reason_excluded', 'N/A')}</div>
                            </div>
                            """
                        scope_html += "</div>"
                    
                    if expansion:
                        total_val = expansion.get('total_if_all_included', 0)
                        total_fmt = f"€{total_val/1e6:.1f}M" if total_val >= 1e6 else f"€{total_val:,.0f}"
                        scope_html += f"""
                        <div style='margin-top: 15px; padding: 12px; background: rgba(0,145,218,0.1); border-radius: 8px;'>
                            <div style='font-size: 0.85em;'><b>Potentiel si tous périmètres inclus:</b> {total_fmt} (Confiance: {expansion.get('confidence', 'N/A')})</div>
                            <div style='font-size: 0.8em; opacity: 0.7; margin-top: 5px;'>{expansion.get('recommendation', '')}</div>
                        </div>
                        """
                    
                    scope_html += "</div>"
                    
                    # 6. VALIDATION CHECKLIST (HTML)
                    val = analysis.get("validation", {})
                    checks = val.get("sanity_checks", [])
                    
                    check_html = "<div class='check-list'>"
                    for c in checks:
                        # Determine Status - handle non-numeric diff values
                        diff = c.get('diff_percentage', 0)
                        # Remove % sign if present and try to convert to float
                        try:
                            if isinstance(diff, str):
                                # Try to extract numeric part
                                diff_clean = diff.replace('%', '').replace('+', '').replace('-', '', 1).strip()
                                if diff_clean.replace('.', '').isdigit():
                                    diff = float(diff.replace('%', ''))
                                else:
                                    diff = None  # Non-numeric value like "N/A"
                            is_ok = diff is None or abs(diff) < 20
                        except (ValueError, TypeError):
                            diff = None
                            is_ok = True  # Default to OK if can't parse
                        
                        status = "ok" if is_ok else "warn"
                        icon = "" if is_ok else ""
                        diff_display = f"{diff}%" if diff is not None else c.get('diff_percentage', 'N/A')
                        
                        check_html += f"""
                        <div class="check-item {status}">
                            <div class="check-icon">{icon}</div>
                            <div style="flex-grow:1;">
                                <div style="font-weight:bold; font-size:0.9em;">{c.get('check_name', 'Check')}</div>
                                <div style="font-size:0.8em; opacity:0.8;">{c.get('explanation', '')}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-weight:bold;">{c.get('comparison_value', 'N/A')}</div>
                                <div style="font-size:0.7em; opacity:0.6;">(Diff: {diff_display})</div>
                            </div>
                        </div>
                        """
                    if not checks:
                        check_html += "<div style='opacity:0.5; font-style:italic;'>Aucun check disponible.</div>"
                    check_html += "</div>"
                    
                    # 7. FINAL RESULT
                    final_val = final_est.get('value', 0)
                    range_low = final_est.get('range_low', 0)
                    range_high = final_est.get('range_high', 0)
                    
                    def fmt_currency(v):
                        if v >= 1e9: return f"€{v/1e9:.1f}B"
                        if v >= 1e6: return f"€{v/1e6:.1f}M"
                        if v >= 1e3: return f"€{v/1e3:.1f}K"
                        return f"€{v:,.0f}"
                    
                    final_html = f"""
                    <div style="background: linear-gradient(135deg, #00338D 0%, #001E55 100%); color: white; padding: 25px; border-radius: 12px;">
                        <div style="font-size: 0.8em; text-transform: uppercase; opacity: 0.8;">Estimation du Marché - {company} ({country}, {year})</div>
                        <div style="font-size: 2.5em; font-weight: bold; margin: 15px 0;">{fmt_currency(final_val)}</div>
                        <div style="font-size: 1em; opacity: 0.9;">
                            Fourchette: <b>{fmt_currency(range_low)}</b> - <b>{fmt_currency(range_high)}</b>
                        </div>
                    </div>
                    """
                    
                    # 8. RELIABILITY
                    rel = analysis.get("reliability", {})
                    conf = rel.get("overall_confidence", "LOW").upper()
                    conf_color = "#00C853" if conf == "HIGH" else "#FFAB00" if conf == "MEDIUM" else "#FF5252"
                    
                    rel_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span>Fiabilité</span>
                            <span style="background: {conf_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">{conf}</span>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="opacity: 0.7;">Qualité données</span>
                                <span>{rel.get('data_quality_score', 'N/A')}%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="opacity: 0.7;">Hypothèses</span>
                                <span>{rel.get('hypothesis_count', 'N/A')}</span>
                            </div>
                        </div>
                        <div style="font-size: 0.85em; color: #FFAB00;">
                            <b>Incertitudes:</b> {', '.join(rel.get('key_uncertainties', [])[:2])}
                        </div>
                    </div>
                    """
                    
                    # 9. SOURCES LIST (HTML) - Enhanced for detailed sources
                    sources = analysis.get("sources_registry", [])
                    sources_html = "<div style='display: grid; gap: 12px;'>"
                    for s in sources:
                        reliability_color = {"HIGH": "#4ADE80", "MEDIUM": "#FFAB00", "LOW": "#F87171"}.get(s.get('reliability', 'MEDIUM'), '#9E9E9E')
                        url = s.get('source_url', '')
                        url_html = f"<a href='{url}' target='_blank' style='color: #0091DA; font-size: 0.75em;'>Voir source →</a>" if url and not url.endswith('...') else ""
                        
                        sources_html += f"""
                        <div style="background: #1E293B; padding: 12px; border-radius: 8px; border-left: 3px solid {reliability_color};">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                <div>
                                    <div style="font-weight: bold; color: #F8FAFC;">{s.get('source_name', s.get('name', 'Source'))}</div>
                                    <div style="font-size: 0.8em; opacity: 0.7;">{s.get('source_full_name', '')}</div>
                                </div>
                                <span style="background: {reliability_color}; color: #0F172A; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold;">{s.get('reliability', 'N/A')}</span>
                            </div>
                            <div style="font-size: 0.85em; color: #CBD5E1; margin-bottom: 5px;">{s.get('source_reference', s.get('details', ''))}</div>
                            <div style="font-size: 0.8em; opacity: 0.7;">Données utilisées: {s.get('data_used', 'N/A')}</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                                <span style="font-size: 0.75em; opacity: 0.6;">Date: {s.get('date', 'N/A')}</span>
                                {url_html}
                            </div>
                        </div>
                        """
                    if not sources:
                        sources_html += "<div style='opacity:0.5; padding: 10px;'>Pas de sources enregistrées.</div>"
                    sources_html += "</div>"
                    
                    # GENERATE SIZING SUMMARY for downstream modules
                    # Use the same path as final_html (calculation.final_estimate)
                    calc_for_summary = analysis.get('calculation', {})
                    final_est_summary = calc_for_summary.get('final_estimate', {})
                    final_val = final_est_summary.get('value', 0)
                    range_low = final_est_summary.get('range_low', 0)
                    range_high = final_est_summary.get('range_high', 0)
                    rel = analysis.get('reliability', {})
                    conf = rel.get('overall_confidence', 'LOW').upper()
                    
                    def fmt_curr(v):
                        if isinstance(v, (int, float)):
                            if v >= 1e9: return f"€{v/1e9:.1f}B"
                            if v >= 1e6: return f"€{v/1e6:.1f}M"
                            if v >= 1e3: return f"€{v/1e3:.1f}K"
                            return f"€{v:,.0f}"
                        return str(v)
                    
                    sizing_summary = f"""ESTIMATION DU MARCHÉ - {company.upper()} ({country.upper()}, {year})
{fmt_curr(final_val)}
Fourchette: {fmt_curr(range_low)} - {fmt_curr(range_high)}
Fiabilité: {conf}""".strip()
                    
                    return (
                        ctx_html,
                        mkt_html,
                        facts_html,       # HTML REPLACEMENT
                        eu_html,
                        ap_html,
                        uv_html,
                        ar_html,
                        calc_html,
                        hyp_html,          # NEW: Hypotheses detailed
                        sens_html,         # NEW: Sensitivity analysis
                        reg_html,          # NEW: Regulatory impact
                        scope_html,        # NEW: Scope analysis
                        final_html,
                        rel_html,
                        check_html,       # HTML REPLACEMENT
                        sources_html,     # HTML REPLACEMENT
                        # === NEW: Global State Updates ===
                        company,          # → state_company
                        country,          # → state_country
                        year,             # → state_year
                        additional,       # → state_context
                        sizing_summary    # → state_sizing_summary
                    )
                
                btn_run_sizing.click(
                    run_contextual_sizing,
                    inputs=[ctx_company, ctx_country, ctx_year, ctx_additional],
                    outputs=[
                        out_context_lock,
                        out_market_definition,
                        out_facts_registry,        # Updated Output
                        out_economic_unit,
                        out_addressable_pop,
                        out_unit_value,
                        out_adoption_rate,
                        out_calculation,
                        out_hypotheses_detailed,   # NEW: Hypotheses
                        out_sensitivity_analysis,  # NEW: Sensitivity
                        out_regulatory_impact,     # NEW: Regulatory
                        out_scope_analysis,        # NEW: Scope
                        out_final_result,
                        out_reliability,
                        out_validation_checklist, # Updated Output
                        out_sources_list,         # Updated Output
                        # === NEW: Global State Updates ===
                        state_company,
                        state_country,
                        state_year,
                        state_context,
                        state_sizing_summary
                    ]
                )

            # ─── ONGLET 2 : SEGMENTATION DES ENTREPRISES CONCURRENTES ───
            with gr.Tab("Structure du marché"):
                gr.Markdown("### Contexte de la segmentation")
                
                # SECTION 1: VERROUILLAGE DU CONTEXTE + MARKET SIZING
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("#### Paramètres")
                        with gr.Row():
                            seg_company = gr.Textbox(
                                label="Entreprise de Référence",
                                placeholder="ex: Doctolib, Alan, Qonto...",
                                value=""
                            )
                            seg_country = gr.Dropdown(
                                choices=["France", "Allemagne", "Pologne", "Espagne", "Italie", "UK", "USA"],
                                label="Pays / Zone",
                                value="France",
                                allow_custom_value=True
                            )
                        with gr.Row():
                            seg_offerings = gr.Textbox(
                                label="Offre / Périmètre Fonctionnel",
                                placeholder="ex: Téléconsultation, Prise de RDV, Gestion de cabinet...",
                                value=""
                            )
                            seg_year = gr.Dropdown(
                                choices=["2024", "2025", "2026"],
                                label="📅 Année",
                                value="2025",
                                allow_custom_value=True
                            )
                        seg_market_sizing = gr.Textbox(
                            label="Résultats du Market Sizing (OBLIGATOIRE)",
                            placeholder="Collez ici les résultats du Market Sizing contextuel : définition du marché, unités économiques, ordres de grandeur, hypothèses structurantes...",
                            lines=5,
                            value=""
                        )
                        btn_run_segmentation = gr.Button("Lancer la segmentation", variant="primary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ##### Introduction
                        On segmente les **ENTREPRISES** qui captent la valeur, 
                        **pas les clients**.
                        
                        ##### 📋 Cette analyse va produire :
                        -  Logique de segmentation retenue
                        -  4-8 segments d'entreprises
                        -  Lien chiffré avec le sizing
                        -  Positionnement de l'entreprise
                        -  Carte du marché par acteurs
                        -  Fiabilité & limites
                        """)
                
                # SECTION 2: CONTEXTE VERROUILLÉ
                with gr.Accordion("1. Contexte", open=True):
                    out_seg_context = gr.HTML()
                
                # SECTION 3: LOGIQUE DE SEGMENTATION (REMPLACEMENT UX)
                with gr.Accordion(" 2. Logique de Segmentation Retenue", open=True):
                    out_seg_logic = gr.HTML()
                    # REMPLACÉ: gr.Dataframe
                    out_seg_axes_matrix = gr.HTML(label="Matrice des Axes")
                
                # SECTION 4: SEGMENTS D'ENTREPRISES
                gr.Markdown("### 3. Segments d'Entreprises (4-8 max)")
                out_seg_cards = gr.HTML(label="Cartes des Segments")
                
                # SECTION 5: DISTRIBUTION DE VALEUR & CARTE
                with gr.Accordion(" 4. Dynamique de Valeur & Carte du Marché", open=True):
                    with gr.Row():
                        out_seg_bubble = gr.Plot(label="Carte du Marché (Positionnement & Valeur)")
                        out_seg_bar = gr.Plot(label="Répartition de la Valeur Captée")
                    out_seg_value_analysis = gr.HTML()

                
                # SECTION 6: POSITIONNEMENT ENTREPRISE
                with gr.Accordion("5. Positionnement", open=True):
                    with gr.Row():
                        out_seg_core = gr.HTML(label="Segments Cœur de Marché")
                        out_seg_adjacent = gr.HTML(label="Adjacents Crédibles")
                        out_seg_out_of_scope = gr.HTML(label="Hors Scope Réaliste")
                
                # SECTION 7: FIABILITÉ
                with gr.Accordion("🔍 6. Fiabilité & Limites", open=False):
                    out_seg_reliability = gr.HTML()
                    with gr.Row():
                        # REMPLACÉ: gr.Dataframes
                        out_seg_logic_flow = gr.HTML(label="Logique Factuelle & Hypothèses")
                
                # HANDLER
                def run_company_segmentation(company, offerings, country, year, market_sizing):
                    if not company.strip() or not offerings.strip():
                        return (
                            "<div style='color:#FF5252; padding:20px;'>Veuillez entrer une entreprise et son offre.</div>",
                            "", None, None, None, None, "", "", "", "", "", None, None
                        )
                    
                    if not market_sizing.strip():
                        return (
                            "<div style='color:#FFAB00; padding:20px;'><b>Market Sizing manquant.</b> Veuillez d'abord exécuter le module Market Sizing Contextuel et coller les résultats ici. La segmentation s'appuie sur ces données.</div>",
                            "", None, None, None, None, "", "", "", "", "", None, None
                        )
                    
                    from strategic_facts_service import strategic_facts_service
                    result = strategic_facts_service.generate_market_segmentation(
                        company_name=company.strip(),
                        offerings=offerings.strip(),
                        country=country.strip(),
                        year=year.strip(),
                        market_sizing_context=market_sizing.strip()
                    )
                    
                    if not result.get("success"):
                        error_msg = result.get("error", "Erreur inconnue")
                        return (
                            f"<div style='color:#FF5252; padding:20px;'>Erreur : {error_msg}</div>",
                            "", None, None, None, None, "", "", "", "", "", None, None
                        )
                    
                    analysis = result.get("analysis", {})
                    
                    # 1. CONTEXT LOCK + SIZING SUMMARY
                    ctx = analysis.get("context_lock", {})
                    ctx_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 4px solid #0091DA;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div><span style="opacity: 0.7;">Entreprise:</span> <b style="color: #0091DA;">{ctx.get('reference_company', 'N/A')}</b></div>
                            <div><span style="opacity: 0.7;">Pays:</span> <b>{ctx.get('country', 'N/A')}</b></div>
                            <div><span style="opacity: 0.7;">Année:</span> <b>{ctx.get('year', 'N/A')}</b></div>
                            <div><span style="opacity: 0.7;">Offre:</span> <b>{ctx.get('offering_scope', 'N/A')}</b></div>
                        </div>
                        <div style="background: rgba(0,145,218,0.1); padding: 15px; border-radius: 8px;">
                            <div style="font-weight: bold; color: #0091DA; margin-bottom: 10px;">📊 Market Sizing de Référence</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div><span style="opacity: 0.7;">Marché Total:</span> <b>{ctx.get('total_market_value', 0):,.0f} {ctx.get('market_unit', 'EUR')}</b></div>
                                <div><span style="opacity: 0.7;">Sizing disponible:</span> <b style="color: {'#00C853' if ctx.get('market_sizing_available') else '#FF5252'}">{'✅ Oui' if ctx.get('market_sizing_available') else '❌ Non'}</b></div>
                            </div>
                            <div style="margin-top: 10px; font-style: italic; opacity: 0.9;">{ctx.get('market_sizing_summary', 'N/A')}</div>
                        </div>
                        {"<div style='color: #FFAB00; margin-top: 10px;'>⚠️ Éléments manquants: " + ', '.join(ctx.get('missing_sizing_elements', [])) + "</div>" if ctx.get('missing_sizing_elements') else ""}
                    </div>
                    """
                    
                    # 2. SEGMENTATION LOGIC WITH VISUAL MATRIX
                    logic = analysis.get("segmentation_logic", {})
                    primary = logic.get("primary_axis", {})
                    secondary = logic.get("secondary_axes", [])
                    rejected = logic.get("rejected_axes", [])
                    
                    logic_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="font-weight: bold; color: #0091DA; font-size: 1.1em; margin-bottom: 15px;">Axe Principal de Segmentation</div>
                        <div style="background: rgba(0,145,218,0.15); padding: 15px; border-radius: 8px; border-left: 3px solid #0091DA;">
                            <div style="font-size: 1.1em; font-weight: bold;">{primary.get('axis_name', 'N/A')}</div>
                            <div style="opacity: 0.8; margin-top: 5px;">Type: <code>{primary.get('axis_type', 'N/A')}</code></div>
                            <div style="margin-top: 10px;"><b>Justification:</b> {primary.get('justification', 'N/A')}</div>
                            <div style="margin-top: 5px; color: #00C853;"><b>Lien avec le sizing:</b> {primary.get('link_to_sizing', 'N/A')}</div>
                        </div>
                    </div>
                    """
                    
                    # AXES MATRIX (HTML)
                    axes_html = "<div class='axes-matrix'>"
                    
                    # Col 1: Kept
                    axes_html += "<div class='axes-col'><div style='font-weight:bold; margin-bottom:10px; color:#00C853;'>Axes Secondaires Retenus</div>"
                    for ax in secondary:
                        axes_html += f"""
                        <div class="axis-card kept">
                            <div style="font-weight: bold;">{ax.get('axis_name', 'N/A')}</div>
                            <div style="font-size: 0.85em; opacity: 0.8;">{ax.get('relevance', '')}</div>
                        </div>
                        """
                    if not secondary:
                        axes_html += "<div style='opacity:0.5'>Aucun axe secondaire.</div>"
                    axes_html += "</div>"
                    
                    # Col 2: Rejected
                    axes_html += "<div class='axes-col'><div style='font-weight:bold; margin-bottom:10px; color:#9E9E9E;'>Axes Éliminés</div>"
                    for ax in rejected:
                        axes_html += f"""
                        <div class="axis-card rejected">
                            <div style="font-weight: bold;">{ax.get('axis_name', 'N/A')}</div>
                            <div style="font-size: 0.85em; opacity: 0.8;">{ax.get('reason', '')}</div>
                        </div>
                        """
                    if not rejected:
                        axes_html += "<div style='opacity:0.5'>Aucun axe rejeté.</div>"
                    axes_html += "</div></div>"
                    
                    
                    # 3. SEGMENT CARDS & CHARTS PREPARATION

                    segments = analysis.get("company_segments", [])
                    
                    # Define consistent color palette
                    import plotly.express as px
                    import plotly.graph_objects as go
                    colors = px.colors.qualitative.Bold  # Strong, distinct colors
                    
                    segment_cards_html = '<div class="segment-grid">'
                    seg_data_for_plots = []
                    
                    if segments:
                        for idx, seg in enumerate(segments):
                            color = colors[idx % len(colors)]
                            seg_id = seg.get("segment_id", "")
                            seg_name = seg.get("segment_name", "Segment Inconnu")
                            rev_model = seg.get("revenue_model", "N/A")
                            logic = seg.get("value_creation_logic", "N/A")
                            e_unit = seg.get("target_economic_unit", "N/A")
                            mkt_share = seg.get("market_share_captured", {})
                            val_captured = mkt_share.get("value", 0)
                            pct_total = mkt_share.get("percentage_of_total", 0)
                            players = ", ".join(seg.get("representative_players", [])[:3])
                            
                            # Format Value
                            val_fmt = f"€{val_captured/1e6:.1f}M" if val_captured else "N/A"
                            
                            # Prepare Data for Plots
                            seg_data_for_plots.append({
                                "name": seg_name,
                                "value": val_captured,
                                "pct": pct_total,
                                "color": color,
                                "id": seg_id
                            })
                            
                            # HTML Card Construction
                            segment_cards_html += f"""
                            <div class="segment-card" style="border-top: 5px solid {color};">
                                <div class="card-header">
                                    <div>
                                        <div class="card-title">{seg_name}</div>
                                        <div style="font-size: 0.8em; opacity: 0.6; font-style: italic;">{rev_model}</div>
                                    </div>
                                    <div class="card-badge" style="color: {color}; border: 1px solid {color};">{seg_id}</div>
                                </div>
                                <div class="card-body">
                                    <div style="font-size: 0.9em; margin-bottom: 12px; line-height: 1.4;">{logic}</div>
                                    
                                    <div class="card-metric" style="border-left: 3px solid {color};">
                                        <div style="font-size: 0.8em; opacity: 0.8;">Valeur Captée</div>
                                        <div class="metric-value" style="color: {color};">{val_fmt}</div>
                                    </div>
                                    
                                    <div style="font-size: 0.8em; display: flex; justify-content: space-between; margin-bottom: 8px;">
                                        <span style="opacity: 0.6;">Part de Marché:</span>
                                        <span style="font-weight: bold;">{pct_total}%</span>
                                    </div>
                                    <div style="font-size: 0.8em; display: flex; justify-content: space-between; margin-bottom: 12px;">
                                        <span style="opacity: 0.6;">Unité Éco:</span>
                                        <span style="font-weight: bold;">{e_unit}</span>
                                    </div>
                                    
                                    <div style="margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05);">
                                        <div style="font-size: 0.75em; text-transform: uppercase; opacity: 0.5; margin-bottom: 4px;">Acteurs Clés</div>
                                        <div style="font-size: 0.85em; color: #E0E0E0;">{players}</div>
                                    </div>
                                </div>
                            </div>
                            """
                    
                    segment_cards_html += '</div>'
                    
                    # 4. VISUALIZATIONS
                    
                    # A. Market Map (Bubble Chart)
                    viz = analysis.get("visualizations", {})
                    market_map = viz.get("market_map", {})
                    
                    if market_map.get("data"):
                        fig_bubble = go.Figure()
                        
                        # Find max size for scaling
                        bubble_data = market_map["data"]
                        max_size = max([pt.get("size", 10) for pt in bubble_data]) if bubble_data else 10
                        
                        for pt in bubble_data:
                            # Match segment to get name and color
                            seg_match = next((s for s in seg_data_for_plots if s["id"] == pt["segment"]), None)
                            seg_name = seg_match["name"] if seg_match else pt["segment"]
                            seg_color = seg_match["color"] if seg_match else "#FFFFFF"
                            
                            fig_bubble.add_trace(go.Scatter(
                                x=[pt.get("x", 0)],
                                y=[pt.get("y", 0)],
                                mode='markers+text',
                                marker=dict(
                                    size=pt.get("size", 20),
                                    sizemode='area',
                                    sizeref=2.*max_size/(60.**2), # Scaling bubble size
                                    sizemin=8,
                                    color=seg_color,
                                    opacity=0.8,
                                    line=dict(width=1, color='white')
                                ),
                                text=[f"<b>{seg_name}</b><br><i>{pt.get('segment', '')}</i>"],
                                textposition="top center",
                                hovertemplate='<b>%{text}</b><br>Intégration: %{x}<br>Valeur: %{y}<extra></extra>',
                                name=seg_name,
                                showlegend=False # Legend handles by the card grid colors
                            ))
                        
                        fig_bubble.update_layout(
                            title=dict(
                                text="<b>Carte Stratégique du Marché</b><br><span style='font-size:0.9em; opacity:0.7'>Positionnement des Modèles Économiques</span>",
                                font=dict(color="white", size=16)
                            ),
                            xaxis=dict(
                                title=market_map.get("x_axis", "Degré d'intégration"),
                                showgrid=True,
                                gridcolor='rgba(255,255,255,0.1)',
                                zeroline=True,
                                zerolinecolor='rgba(255,255,255,0.2)'
                            ),
                            yaxis=dict(
                                title=market_map.get("y_axis", "Valeur captée"),
                                showgrid=True,
                                gridcolor='rgba(255,255,255,0.1)',
                                zeroline=True,
                                zerolinecolor='rgba(255,255,255,0.2)'
                            ),
                            plot_bgcolor="#1E1E1E",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#E0E0E0", family="Inter"),
                            margin=dict(l=40, r=40, t=60, b=40)
                        )
                    else:
                        fig_bubble = go.Figure()
                        fig_bubble.update_layout(title="Données de carte non disponibles", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))

                    # B. Value Distribution (Horizontal Bar Chart)
                    if seg_data_for_plots:
                        # Sort by value
                        seg_data_sorted = sorted(seg_data_for_plots, key=lambda x: x["value"] if x["value"] else 0, reverse=False) # Ascending for horizontal bar
                        
                        names = [d["name"] for d in seg_data_sorted]
                        values = [d["value"] for d in seg_data_sorted]
                        pcts = [d["pct"] for d in seg_data_sorted]
                        colors_mapped = [d["color"] for d in seg_data_sorted]
                        text_labels = [f" {v/1e6:.1f} M€ ({p}%)" for v, p in zip(values, pcts)]
                        
                        fig_bar = go.Figure(go.Bar(
                            x=values,
                            y=names,
                            orientation='h',
                            text=text_labels,
                            textposition='outside', # Text outside bar for readability
                            marker=dict(color=colors_mapped, opacity=0.9, line=dict(width=0))
                        ))
                        
                        fig_bar.update_layout(
                            title=dict(
                                text="<b>Répartition de la Valeur Captée</b><br><span style='font-size:0.9em; opacity:0.7'>Par Segment d'Entreprise</span>",
                                font=dict(color="white", size=16)
                            ),
                            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Valeur (EUR)"),
                            yaxis=dict(showgrid=False),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#E0E0E0", family="Inter"),
                            margin=dict(l=20, r=20, t=60, b=20),
                            uniformtext_minsize=8, 
                            uniformtext_mode='hide'
                        )
                    else:
                        fig_bar = go.Figure()
                        fig_bar.update_layout(title="Pas de données", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))


                    # Value distribution analysis
                    dist = analysis.get("market_value_distribution", {})
                    value_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px; margin-top: 15px; border-left: 4px solid #FFAB00;">
                        <div style="font-weight: bold; margin-bottom: 5px; color: #FFAB00;">📈 Analyse de Concentration & Tendance</div>
                        <div style="margin-bottom: 10px; opacity: 0.9;">{dist.get('concentration_analysis', 'N/A')}</div>
                        <div style="padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <span style="opacity: 0.7;">Migration de Valeur:</span> <b>{dist.get('value_migration_trends', 'N/A')}</b>
                        </div>
                    </div>
                    """
                    
                    # 5. COMPANY POSITIONING
                    pos = analysis.get("reference_company_positioning", {})
                    
                    # Core segments
                    core_ids = pos.get("core_market_segments", [])
                    current = pos.get("current_segments", [])
                    core_html = "<div style='background: rgba(0,145,218,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #0091DA;'><div style='font-weight: bold; margin-bottom: 10px;'>Cœur de Marché</div>"
                    for c in current:
                        if c.get("segment_id") in core_ids:
                            # Find segment name
                            matched = next((s for s in segments if s.get("segment_id") == c.get("segment_id")), None)
                            seg_name = matched.get("segment_name", c.get("segment_id")) if matched else c.get("segment_id")
                            
                            core_html += f"<div style='padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border-radius: 4px;'><b>{seg_name}</b><br><span style='opacity: 0.8;'>Présence: {c.get('presence_level', 'N/A')} | Part: ~{c.get('estimated_share_in_segment', 0)}%</span></div>"
                    core_html += "</div>"
                    
                    # Adjacent segments
                    adjacent = pos.get("credible_adjacent_segments", [])
                    adj_html = "<div style='background: rgba(0,200,83,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #00C853;'><div style='font-weight: bold; margin-bottom: 10px;'>Adjacents Crédibles</div>"
                    for a in adjacent:
                        matched = next((s for s in segments if s.get("segment_id") == a.get("segment_id")), None)
                        seg_name = matched.get("segment_name", a.get("segment_id")) if matched else a.get("segment_id")
                        
                        adj_html += f"<div style='padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border-radius: 4px;'><b>{seg_name}</b><br><span style='opacity: 0.8;'>Faisabilité: {a.get('expansion_feasibility', 'N/A')}</span><br><i>{a.get('strategic_rationale', '')}</i></div>"
                    adj_html += "</div>"
                    
                    # Out of scope
                    oos = pos.get("out_of_scope_segments", [])
                    oos_html = "<div style='background: rgba(255,82,82,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #FF5252;'><div style='font-weight: bold; margin-bottom: 10px;'>Hors Périmètre</div>"
                    for o in oos:
                        matched = next((s for s in segments if s.get("segment_id") == o.get("segment_id")), None)
                        seg_name = matched.get("segment_name", o.get("segment_id")) if matched else o.get("segment_id")
                        
                        oos_html += f"<div style='padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border-radius: 4px;'><b>{seg_name}</b><br><i>{o.get('reason', 'N/A')}</i></div>"
                    oos_html += "</div>"
                    
                    # 6. RELIABILITY
                    rel = analysis.get("reliability", {})
                    conf = rel.get("overall_confidence", "LOW").upper()
                    conf_color = "#00C853" if conf == "HIGH" else "#FFAB00" if conf == "MEDIUM" else "#FF5252"
                    
                    rel_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span style="font-weight: bold; font-size: 1.1em;">Fiabilité Globale</span>
                            <span style="background: {conf_color}; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold;">{conf}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Granularité Sizing:</span> <b>{rel.get('sizing_granularity', 'N/A')}</b>
                            </div>
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Traçabilité Hypothèses:</span> <b>{rel.get('hypothesis_traceability', 'N/A')}</b>
                            </div>
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Clarté Frontières:</span> <b>{rel.get('segment_boundary_clarity', 'N/A')}</b>
                            </div>
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Cohérence Concurrentielle:</span> <b>{rel.get('local_competitive_coherence', 'N/A')}</b>
                            </div>
                        </div>
                        <div style="font-size: 0.95em; margin-bottom: 10px;">{rel.get('confidence_justification', 'N/A')}</div>
                        <div style="color: #FFAB00; font-size: 0.85em;">
                            <b>Limitations:</b> {', '.join(rel.get('key_limitations', []))}
                        </div>
                    </div>
                    """
                    
                    # 7. LOGICAL FLOW OF FACTS & HYPOTHESES (HTML)
                    fh = analysis.get("facts_and_hypotheses", {})
                    sizing_facts = fh.get("sizing_facts_used", [])
                    new_hyps = fh.get("new_hypotheses", [])
                    
                    logic_flow_html = """
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="background: rgba(0,145,218,0.05); padding: 15px; border-radius: 8px;">
                            <div style="font-weight: bold; color: #0091DA; margin-bottom: 10px;">🏗️ Facts Structurants (Sizing)</div>
                            <div class="source-list">
                    """
                    
                    for f in sizing_facts:
                        logic_flow_html += f"""
                        <div class="source-item">
                            <div style="font-weight: bold; font-size: 0.9em;">{f.get('fact', 'N/A')}</div>
                            <div style="font-size: 0.8em; opacity: 0.8; margin-top: 3px;">Implication: {f.get('segmentation_implication', 'N/A')}</div>
                        </div>
                        """
                    if not sizing_facts:
                         logic_flow_html += "<div style='opacity:0.5'>Aucun fact spécifique.</div>"
                    
                    logic_flow_html += """
                            </div>
                        </div>
                        <div style="background: rgba(255,171,0,0.05); padding: 15px; border-radius: 8px;">
                            <div style="font-weight: bold; color: #FFAB00; margin-bottom: 10px;">🧪 Nouvelles Hypothèses</div>
                            <div class="source-list">
                    """
                    
                    for h in new_hyps:
                         logic_flow_html += f"""
                        <div class="source-item" style="border-left-color: #FFAB00;">
                            <div style="font-weight: bold; font-size: 0.9em;">{h.get('hypothesis', 'N/A')}</div>
                            <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 0.8em;">
                                <span style="opacity: 0.7;">Impact: <b>{h.get('impact_level', 'medium').upper()}</b></span>
                                <span style="opacity: 0.7;">Sensibilité: <b>{h.get('sensitivity', 'medium').upper()}</b></span>
                            </div>
                        </div>
                        """
                    
                    if not new_hyps:
                         logic_flow_html += "<div style='opacity:0.5'>Aucune hypothèse majeure.</div>"

                    logic_flow_html += """
                            </div>
                        </div>
                    </div>
                    """
                    
                    # GENERATE SEGMENTATION SUMMARY for Competitive Analysis
                    seg_summary_lines = [f"SEGMENTATION - {company.upper()} ({country}, {year})"]
                    
                    # Core market segments
                    core_names = []
                    for c in current:
                        if c.get("segment_id") in core_ids:
                            matched = next((s for s in segments if s.get("segment_id") == c.get("segment_id")), None)
                            if matched:
                                core_names.append(matched.get("segment_name", c.get("segment_id")))
                    if core_names:
                        seg_summary_lines.append(f"Marché ciblé: {', '.join(core_names[:3])}")
                    
                    # Niche/adjacent info
                    adj_names = []
                    for a in adjacent:
                        matched = next((s for s in segments if s.get("segment_id") == a.get("segment_id")), None)
                        if matched:
                            adj_names.append(matched.get("segment_name", a.get("segment_id")))
                    if adj_names:
                        seg_summary_lines.append(f"Niche adjacente: {', '.join(adj_names[:2])}")
                    
                    seg_summary = "\n".join(seg_summary_lines)
                    
                    return (
                        ctx_html,
                        logic_html,
                        axes_html,           # HTML REPLACEMENT
                        segment_cards_html,
                        fig_bar,
                        fig_bubble,
                        value_html,
                        core_html,
                        adj_html,
                        oos_html,
                        rel_html,
                        logic_flow_html,      # HTML REPLACEMENT
                        seg_summary           # For state_seg_summary
                    )
                
                btn_run_segmentation.click(
                    run_company_segmentation,
                    inputs=[seg_company, seg_offerings, seg_country, seg_year, seg_market_sizing],
                    outputs=[
                        out_seg_context,
                        out_seg_logic,
                        out_seg_axes_matrix, # Updated output name/type
                        out_seg_cards,
                        out_seg_bar,
                        out_seg_bubble,
                        out_seg_value_analysis,
                        out_seg_core,
                        out_seg_adjacent,
                        out_seg_out_of_scope,
                        out_seg_reliability,
                        out_seg_logic_flow,   # Merged/Updated output name/type
                        state_seg_summary     # Segmentation summary state
                    ]
                )

            # ─── ONGLET 3 : ANALYSE CONCURRENTIELLE (REFACTORED: Facts-First) ───
            with gr.Tab("Concurrence"):
                gr.Markdown("### Analyse concurrentielle")
                
                # CONTEXT INPUTS (Like other modules)
                with gr.Row():
                    comp_company = gr.Textbox(label="Entreprise de Référence", placeholder="Ex: Salesforce")
                    comp_country = gr.Textbox(label="Pays/Marché", placeholder="Ex: France")
                    comp_year = gr.Textbox(label="Année", placeholder="Ex: 2024")
                
                with gr.Row():
                    comp_sizing_ref = gr.Textbox(
                        label="Contexte Market Sizing (optionnel)", 
                        placeholder="Coller ici un résumé du market sizing...",
                        lines=2
                    )
                    comp_seg_ref = gr.Textbox(
                        label="Contexte Segmentation (optionnel)", 
                        placeholder="Coller ici un résumé de la segmentation...",
                        lines=2
                    )
                
                btn_comp_run = gr.Button("Lancer l'analyse", variant="primary")
                
                # CONTEXT SUMMARY
                with gr.Accordion("1. Contexte", open=True):
                    out_comp_context = gr.HTML()
                
                # BLOCK 1: ACTORS MAPPING (Cards)
                with gr.Accordion("2. Cartographie des Acteurs", open=True):
                    out_actors_cards = gr.HTML(label="Acteurs Identifiés")
                
                # BLOCK 2: OFFERINGS BENCHMARK (Visual Matrix)
                with gr.Accordion("3. Benchmark des Offres", open=True):
                    gr.Markdown("*Comparaison fonctionnelle: ✓ Confirmé | ~ Déclaré | ✗ Absent*")
                    out_offerings_html = gr.HTML(label="Matrice des Fonctionnalités")
                
                # BLOCK 3: POSITIONING (Map + Clusters)
                with gr.Accordion("4. Positionnement", open=True):
                    with gr.Row():
                        out_positioning_plot = gr.Plot(label="Carte de Positionnement")
                        out_clusters_html = gr.HTML(label="Clusters de Valeur")
                
                # BLOCK 4: MARKET GAPS
                with gr.Accordion("5. Lecture de la Demande (Gaps)", open=True):
                    out_gaps_html = gr.HTML(label="Besoins vs Couverture")
                
                # BLOCK 5: MARKET TRENDS (replaces recommendation)
                gr.Markdown("### 6. Tendances clés du marché")
                out_trends_html = gr.HTML()
                
                # RELIABILITY & SOURCES
                with gr.Accordion("7. Fiabilité & Sources", open=False):
                    out_reliability_html = gr.HTML()
                    out_sources_html = gr.HTML(label="Registre des Sources")
                
                # HANDLER
                def run_competitive_analysis(company, country, year, sizing_ctx, seg_ctx):
                    import plotly.express as px
                    import plotly.graph_objects as go
                    from strategic_facts_service import strategic_facts_service
                    
                    if not company or not country or not year:
                        return (
                            "<div style='color: #FF5252;'>Veuillez remplir tous les champs obligatoires (Entreprise, Pays, Année).</div>",
                            "", "", None, "", "", "", "", ""
                        )
                    
                    # 1. Call the new dynamic service
                    result = strategic_facts_service.generate_competitive_analysis(
                        company_name=company,
                        country=country,
                        year=year,
                        market_sizing_context=sizing_ctx,
                        segmentation_context=seg_ctx
                    )
                    
                    if not result.get("success"):
                        error_msg = result.get("error", "Erreur inconnue")
                        return (
                            f"<div style='color: #FF5252;'>Erreur: {error_msg}</div>",
                            "", "", None, "", "", "", "", ""
                        )
                    
                    analysis = result.get("analysis", {})
                    
                    # 2. CONTEXT SUMMARY HTML
                    ctx = analysis.get("context_summary", {})
                    ctx_html = f"""
                    <div style="background: rgba(0,145,218,0.1); padding: 15px; border-radius: 10px; border-left: 3px solid #0091DA;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: bold; font-size: 1.2em;">🏢 {ctx.get('reference_company', company)}</div>
                                <div style="opacity: 0.8; margin-top: 5px;">{ctx.get('market_scope', 'Périmètre non défini')}</div>
                            </div>
                            <div style="text-align: right; opacity: 0.7;">
                                <div>📅 {ctx.get('analysis_date', year)}</div>
                                <div>🌍 {country}</div>
                            </div>
                        </div>
                    </div>
                    """
                    
                    # 3. ACTORS CARDS HTML
                    actors = analysis.get("actors", [])
                    actors_html = "<div class='actor-grid'>"
                    for actor in actors:
                        typology = actor.get("typology", "Unknown").lower()
                        typology_class = f"typology-{typology}" if typology in ["leader", "challenger", "niche", "emergent"] else "typology-niche"
                        
                        actors_html += f"""
                        <div class="actor-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                                <div style="font-weight: bold; font-size: 1.1em; color: white;">{actor.get('name', 'N/A')}</div>
                                <span class="actor-typology {typology_class}">{actor.get('typology', 'N/A')}</span>
                            </div>
                            <div style="font-size: 0.85em; color: #B0B0B0; margin-bottom: 8px;">{actor.get('core_offering', 'N/A')}</div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.8em; opacity: 0.7;">
                                <span>{actor.get('geography', 'N/A')}</span>
                                <span>{actor.get('revenue_order', 'N/A')}</span>
                            </div>
                            <div style="margin-top: 8px; font-size: 0.75em; opacity: 0.5;">Source: {actor.get('source', 'Analyse')}</div>
                        </div>
                        """
                    actors_html += "</div>"
                    
                    # 4. OFFERINGS MATRIX HTML
                    bench = analysis.get("offerings_benchmark", {})
                    features = bench.get("key_features", [])
                    matrix = bench.get("matrix", [])
                    
                    offerings_html = "<table class='offerings-matrix'><thead><tr><th>Acteur</th>"
                    for feat in features:
                        offerings_html += f"<th>{feat}</th>"
                    offerings_html += "</tr></thead><tbody>"
                    
                    for row in matrix:
                        offerings_html += f"<tr><td style='text-align:left; font-weight:bold;'>{row.get('actor', 'N/A')}</td>"
                        actor_feats = row.get("features", {})
                        for feat in features:
                            feat_data = actor_feats.get(feat, {})
                            status = feat_data.get("status", "absent") if isinstance(feat_data, dict) else feat_data
                            
                            if status == "confirmed":
                                icon = "✓"
                                css_class = "feat-confirmed"
                            elif status == "declared":
                                icon = "~"
                                css_class = "feat-declared"
                            else:
                                icon = "✗"
                                css_class = "feat-absent"
                            
                            offerings_html += f"<td class='{css_class}'>{icon}</td>"
                        offerings_html += "</tr>"
                    offerings_html += "</tbody></table>"
                    
                    # 5. POSITIONING PLOT + CLUSTERS HTML
                    clusters = analysis.get("positioning_clusters", [])
                    
                    # Create Plotly scatter for positioning
                    cluster_colors = {
                        "Cost Leader": "#00C853",
                        "Premium": "#0091DA",
                        "Innovator": "#6200EA",
                        "Service-Centric": "#FFAB00",
                        "Generalist": "#9E9E9E"
                    }
                    
                    if clusters:
                        # Map integration level to X and economic model to Y (simple heuristic)
                        x_map = {"Verticale": 0.8, "Horizontale": 0.3, "Spécialisée": 0.5}
                        y_map = {"SaaS": 0.8, "License": 0.3, "Usage": 0.5, "Hybrid": 0.6}
                        
                        fig_pos = go.Figure()
                        for c in clusters:
                            x = x_map.get(c.get("integration_level", "Horizontale"), 0.5) + (hash(c.get("actor", "")) % 10) / 50
                            y = y_map.get(c.get("economic_model", "Hybrid"), 0.5) + (hash(c.get("claimed_value", "")) % 10) / 50
                            color = cluster_colors.get(c.get("cluster", "Generalist"), "#9E9E9E")
                            
                            fig_pos.add_trace(go.Scatter(
                                x=[x], y=[y],
                                mode="markers+text",
                                marker=dict(size=20, color=color, opacity=0.8),
                                text=[c.get("actor", "")],
                                textposition="top center",
                                name=c.get("cluster", ""),
                                hovertemplate=f"<b>{c.get('actor')}</b><br>Cluster: {c.get('cluster')}<br>Proposition: {c.get('claimed_value')}<extra></extra>"
                            ))
                        
                        fig_pos.update_layout(
                            title="Carte de Positionnement Concurrentiel",
                            xaxis_title="Niveau d'Intégration →",
                            yaxis_title="Modèle Économique →",
                            showlegend=False,
                            paper_bgcolor="#121212",
                            plot_bgcolor="#1E1E1E",
                            font=dict(color="white"),
                            xaxis=dict(showgrid=False, range=[0, 1]),
                            yaxis=dict(showgrid=False, range=[0, 1])
                        )
                    else:
                        fig_pos = go.Figure()
                        fig_pos.update_layout(
                            title="Données insuffisantes",
                            paper_bgcolor="#121212",
                            plot_bgcolor="#1E1E1E",
                            font=dict(color="white")
                        )
                    
                    # Clusters HTML
                    clusters_html = "<div class='source-list'>"
                    for c in clusters:
                        color = cluster_colors.get(c.get("cluster", "Generalist"), "#9E9E9E")
                        clusters_html += f"""
                        <div class="source-item" style="border-left: 3px solid {color};">
                            <div style="font-weight: bold;">{c.get('actor', 'N/A')}</div>
                            <div style="font-size: 0.85em; opacity: 0.8; margin: 5px 0;">{c.get('claimed_value', 'N/A')}</div>
                            <div style="display: flex; gap: 10px; font-size: 0.8em;">
                                <span style="background: {color}; padding: 2px 6px; border-radius: 4px; color: white;">{c.get('cluster', 'N/A')}</span>
                                <span style="opacity: 0.6;">{c.get('integration_level', 'N/A')} | {c.get('economic_model', 'N/A')}</span>
                            </div>
                        </div>
                        """
                    clusters_html += "</div>"
                    
                    # 6. GAPS HTML
                    expectations = analysis.get("market_expectations", [])
                    gaps_html = "<div class='gap-grid'>"
                    for exp in expectations:
                        coverage = exp.get("coverage", "unknown")
                        if coverage == "met":
                            gap_class = "gap-met"
                            badge_class = "badge-met"
                            badge_text = "✓ Couvert"
                        elif coverage == "partial":
                            gap_class = "gap-partial"
                            badge_class = "badge-partial"
                            badge_text = "~ Partiel"
                        else:
                            gap_class = "gap-unmet"
                            badge_class = "badge-unmet"
                            badge_text = "✗ Gap"
                        
                        importance = exp.get("importance", "Medium")
                        imp_indicator = "🔴" if importance == "Critical" else "🟡" if importance == "High" else "⚪"
                        
                        gaps_html += f"""
                        <div class="gap-card {gap_class}">
                            <div style="flex-grow: 1;">
                                <div style="font-weight: bold;">{imp_indicator} {exp.get('criterion', 'N/A')}</div>
                                <div style="font-size: 0.85em; opacity: 0.8; margin-top: 3px;">{exp.get('explanation', '')}</div>
                            </div>
                            <span class="gap-status-badge {badge_class}">{badge_text}</span>
                        </div>
                        """
                    gaps_html += "</div>"
                    
                    # 7. MARKET TRENDS HTML (replaces recommendation)
                    # Call the Market Trends generator service
                    trends_result = strategic_facts_service.generate_market_trends(
                        company_name=company,
                        country=country,
                        year=year,
                        market_sizing_context=sizing_ctx,
                        segmentation_context=seg_ctx,
                        competitive_context=str(analysis.get('context_summary', {}))
                    )
                    
                    trends_html = ""
                    if trends_result.get("success"):
                        trends = trends_result.get("analysis", {})
                        market_trends = trends.get("market_trends", [])
                        weak_signals = trends.get("weak_signals", [])
                        debates = trends.get("market_debates", [])
                        summary = trends.get("structural_vs_cyclical_summary", {})
                        
                        # Build trends cards
                        driver_colors = {
                            "technologique": "#6200EA",
                            "réglementaire": "#0091DA",
                            "économique": "#FFAB00",
                            "comportemental": "#00C853",
                            "ESG": "#4CAF50"
                        }
                        maturity_badges = {
                            "émergente": ("", "#4CAF50"),
                            "en accélération": ("", "#FF9800"),
                            "mature": ("", "#9E9E9E")
                        }
                        
                        trends_html = f"""
                        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 20px; border-radius: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <div style="font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; color: #94A3B8;">Tendances du Marché • Horizon 2-5 ans</div>
                                <div style="display: flex; gap: 10px;">
                                    <span style="padding: 4px 10px; border-radius: 10px; font-size: 0.75em; background: rgba(100,200,100,0.2); color: #4ADE80;">{summary.get('structural_trends_count', 0)} Structurelles</span>
                                    <span style="padding: 4px 10px; border-radius: 10px; font-size: 0.75em; background: rgba(255,171,0,0.2); color: #FFAB00;">{summary.get('cyclical_trends_count', 0)} Conjoncturelles</span>
                                </div>
                            </div>
                        """
                        
                        # Trend cards
                        trends_html += "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;'>"
                        for tr in market_trends:
                            driver = tr.get("driver", "technologique")
                            color = driver_colors.get(driver, "#6200EA")
                            mat = tr.get("maturity", "émergente")
                            mat_icon, mat_color = maturity_badges.get(mat, ("", "#4CAF50"))
                            trend_type = tr.get("type", "structurelle")
                            type_badge = "📊" if trend_type == "structurelle" else "📈"
                            
                            trends_html += f"""
                            <div style="background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 15px; border-left: 4px solid {color};">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; text-transform: uppercase;">{driver}</span>
                                        <span style="background: {mat_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em;">{mat_icon} {mat}</span>
                                    </div>
                                    <span style="opacity: 0.6; font-size: 0.75em;">{type_badge} {trend_type.capitalize()}</span>
                                </div>
                                <div style="font-weight: bold; color: #F8FAFC; margin-bottom: 8px;">{tr.get('title', 'N/A')}</div>
                                <div style="font-size: 0.85em; color: #CBD5E1; line-height: 1.5; margin-bottom: 10px;">{tr.get('description', 'N/A')}</div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.75em; opacity: 0.7;">
                                    <span>⏱{tr.get('horizon', 'moyen terme')}</span>
                                    <span>{tr.get('geographic_scope', country)}</span>
                                </div>
                                {f'<div style="margin-top: 8px; font-size: 0.7em; color: #FFAB00;">⚠️ Incertitude: {tr.get("uncertainty_reason", "")}</div>' if tr.get('uncertainty_level') in ['moyen', 'élevé'] else ''}
                            </div>
                            """
                        trends_html += "</div>"
                        
                        # Weak signals section
                        if weak_signals:
                            trends_html += """
                            <div style="margin-top: 20px; padding: 15px; background: rgba(255,171,0,0.1); border-radius: 8px; border: 1px dashed #FFAB00;">
                                <div style="font-weight: bold; color: #FFAB00; margin-bottom: 10px;">Signaux Faibles</div>
                                <div style="display: grid; gap: 10px;">
                            """
                            for sig in weak_signals:
                                trends_html += f"""
                                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                                    <div style="font-weight: bold; color: #F8FAFC; font-size: 0.9em;">{sig.get('signal', 'N/A')}</div>
                                    <div style="font-size: 0.8em; color: #CBD5E1; margin-top: 5px;">Impact potentiel: {sig.get('potential_impact', 'N/A')}</div>
                                    <div style="font-size: 0.75em; opacity: 0.6; margin-top: 3px;">Horizon: {sig.get('emergence_timeline', 'N/A')}</div>
                                </div>
                                """
                            trends_html += "</div></div>"
                        
                        # Market debates section
                        if debates:
                            trends_html += """
                            <div style="margin-top: 20px; padding: 15px; background: rgba(0,145,218,0.1); border-radius: 8px; border: 1px dashed #0091DA;">
                                <div style="font-weight: bold; color: #0091DA; margin-bottom: 10px;">⚖️ Zones d'Incertitude / Débats du Marché</div>
                            """
                            for deb in debates:
                                trends_html += f"""
                                <div style="margin-bottom: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                    <div style="font-weight: bold; color: #F8FAFC; font-size: 0.9em;">{deb.get('topic', 'N/A')}</div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; font-size: 0.8em;">
                                        <div style="padding: 8px; background: rgba(100,200,100,0.1); border-radius: 4px;">
                                            <div style="color: #4ADE80; font-weight: bold;">Position A</div>
                                            <div style="color: #CBD5E1;">{deb.get('position_a', 'N/A')}</div>
                                        </div>
                                        <div style="padding: 8px; background: rgba(255,82,82,0.1); border-radius: 4px;">
                                            <div style="color: #F87171; font-weight: bold;">Position B</div>
                                            <div style="color: #CBD5E1;">{deb.get('position_b', 'N/A')}</div>
                                        </div>
                                    </div>
                                    <div style="font-size: 0.75em; opacity: 0.6; margin-top: 5px;">Consensus: {deb.get('consensus_level', 'N/A')}</div>
                                </div>
                                """
                            trends_html += "</div>"
                        
                        trends_html += "</div>"
                    else:
                        trends_html = f"<div style='color: #FFAB00; padding: 15px;'>⚠️ Analyse des tendances non disponible: {trends_result.get('error', 'Erreur inconnue')}</div>"
                    
                    # 8. RELIABILITY HTML
                    rel = analysis.get("reliability", {})
                    rel_conf = rel.get("overall_confidence", "LOW").upper()
                    rel_color = "#00C853" if rel_conf == "HIGH" else "#FFAB00" if rel_conf == "MEDIUM" else "#FF5252"
                    
                    rel_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span style="font-weight: bold; font-size: 1.1em;">Fiabilité de l'Analyse</span>
                            <span style="background: {rel_color}; color: white; padding: 6px 15px; border-radius: 15px; font-weight: bold;">{rel_conf}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Sources primaires:</span> <b>{len(rel.get('primary_sources', []))}</b>
                            </div>
                            <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                                <span style="opacity: 0.7;">Fraîcheur:</span> <b>{rel.get('data_freshness', 'N/A')}</b>
                            </div>
                        </div>
                        <div style="font-size: 0.85em; color: #FFAB00;">
                            <b>Limitations:</b> {', '.join(rel.get('key_limitations', [])[:2])}
                        </div>
                    </div>
                    """
                    
                    # 9. SOURCES HTML
                    facts = result.get("facts", [])
                    sources_html = "<div class='source-list'>"
                    for f in facts:
                        sources_html += f"""
                        <div class="source-item">
                            <div class="source-header">
                                <span class="source-badge secondary">{f.get('category', 'N/A').upper()}</span>
                                <span>Confiance: <b style="color:{'#00C853' if f.get('confidence')=='high' else '#FFAB00'}">{f.get('confidence', 'medium').upper()}</b></span>
                            </div>
                            <div style="font-weight: bold; margin: 4px 0; color: #E0E0E0;">{f.get('key', 'Fact').replace('_', ' ').capitalize()}</div>
                            <div style="font-size: 0.9em; color: white;">{f.get('value', 'N/A')}</div>
                            <div style="font-size: 0.8em; opacity: 0.6; margin-top: 5px;">{f.get('notes', '')}</div>
                        </div>
                        """
                    sources_html += "</div>"
                    
                    return (
                        ctx_html,
                        actors_html,
                        offerings_html,
                        fig_pos,
                        clusters_html,
                        gaps_html,
                        trends_html,
                        rel_html,
                        sources_html
                    )
                
                btn_comp_run.click(
                    run_competitive_analysis,
                    inputs=[comp_company, comp_country, comp_year, comp_sizing_ref, comp_seg_ref],
                    outputs=[
                        out_comp_context,
                        out_actors_cards,
                        out_offerings_html,
                        out_positioning_plot,
                        out_clusters_html,
                        out_gaps_html,
                        out_trends_html,
                        out_reliability_html,
                        out_sources_html
                    ]
                )
        
        # ═══════════════════════════════════════════════════════════════════════
        # CONTEXT PROPAGATION: States → Input Fields (other tabs)
        # ═══════════════════════════════════════════════════════════════════════
        
        # When state_company changes, update seg_company and comp_company
        state_company.change(
            fn=lambda x: (x, x),
            inputs=[state_company],
            outputs=[seg_company, comp_company]
        )
        
        # When state_country changes, update seg_country and comp_country
        state_country.change(
            fn=lambda x: (x, x),
            inputs=[state_country],
            outputs=[seg_country, comp_country]
        )
        
        # When state_year changes, update seg_year and comp_year
        state_year.change(
            fn=lambda x: (x, x),
            inputs=[state_year],
            outputs=[seg_year, comp_year]
        )
        
        # When state_context (offerings) changes, update seg_offerings
        state_context.change(
            fn=lambda x: x,
            inputs=[state_context],
            outputs=[seg_offerings]
        )
        
        # When state_sizing_summary changes, update seg_market_sizing and comp_sizing_ref
        state_sizing_summary.change(
            fn=lambda x: (x, x),
            inputs=[state_sizing_summary],
            outputs=[seg_market_sizing, comp_sizing_ref]
        )
        
        # When state_seg_summary changes, update comp_seg_ref
        state_seg_summary.change(
            fn=lambda x: x,
            inputs=[state_seg_summary],
            outputs=[comp_seg_ref]
        )

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