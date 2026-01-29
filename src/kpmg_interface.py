
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
            
            # ─── ONGLET 1 : MARKET SIZING CONTEXTUEL (NOUVELLE MÉTHODOLOGIE) ───
            with gr.Tab("📊 Market Sizing Contextuel"):
                gr.Markdown("""
                ### 🎓 Estimation de Marché Contextuelle
                
                > **Méthodologie rigoureuse** : On part d'une entreprise cible, d'un pays et d'une année pour reconstruire
                > le marché de façon bottom-up, avec des facts locaux traçables et des hypothèses explicites.
                """)
                
                # SECTION 1: VERROUILLAGE DU CONTEXTE
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("##### 1️⃣ Verrouillage du Contexte (Obligatoire)")
                        with gr.Row():
                            ctx_company = gr.Textbox(
                                label="🏢 Entreprise Cible",
                                placeholder="ex: Doctolib, Alan, Qonto...",
                                value=""
                            )
                            ctx_country = gr.Dropdown(
                                choices=["France", "Allemagne", "Pologne", "Espagne", "Italie", "Royaume-Uni", "États-Unis", "Brésil", "Japon"],
                                label="🌍 Pays / Zone",
                                value="France",
                                allow_custom_value=True
                            )
                            ctx_year = gr.Dropdown(
                                choices=["2024", "2025", "2026", "2027", "2028"],
                                label="📅 Année",
                                value="2025",
                                allow_custom_value=True
                            )
                        
                        ctx_additional = gr.Textbox(
                            label="📝 Contexte Additionnel (offres, modèle éco, secteur...)",
                            placeholder="ex: SaaS B2B, téléconsultation médicale, prise de RDV...",
                            lines=2,
                            value=""
                        )
                        
                        btn_run_sizing = gr.Button("🚀 Lancer l'Estimation Bottom-Up", variant="primary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ##### 📋 Cette analyse va produire :
                        - ✅ Verrouillage du contexte
                        - ✅ Définition du marché spécifique
                        - ✅ Facts locaux traçables
                        - ✅ Reconstruction bottom-up
                        - ✅ Calcul explicite
                        - ✅ Validation par sanity checks
                        - ✅ Évaluation de fiabilité
                        """)
                
                # SECTION 2: CONTEXTE VERROUILLÉ
                with gr.Accordion("📌 1. Contexte Verrouillé", open=True):
                    out_context_lock = gr.HTML()
                
                # SECTION 3: DÉFINITION DU MARCHÉ
                with gr.Accordion("🎯 2. Définition du Marché Contextuel", open=True):
                    out_market_definition = gr.HTML()
                
                # SECTION 4: FACTS UTILISÉS
                with gr.Accordion("📚 3. Facts Locaux Mobilisés", open=True):
                    out_facts_local = gr.Dataframe(label="Registre des Facts", interactive=False)
                
                # SECTION 5: RECONSTRUCTION BOTTOM-UP
                with gr.Accordion("🔧 4. Reconstruction Bottom-Up Locale", open=True):
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
                with gr.Accordion("🧮 5. Calcul Explicite", open=True):
                    out_calculation = gr.HTML()
                
                # SECTION 7: VALIDATION
                with gr.Accordion("✅ 6. Validation & Sanity Checks", open=True):
                    out_validation = gr.Dataframe(label="Comparaisons", interactive=False)
                
                # SECTION 8: RÉSULTAT FINAL
                gr.Markdown("### 🏁 Résultat de l'Estimation")
                with gr.Row():
                    with gr.Column(scale=2):
                        out_final_result = gr.HTML()
                    with gr.Column(scale=1):
                        out_reliability = gr.HTML()
                
                # SECTION 9: SOURCES
                with gr.Accordion("📑 7. Registre des Sources", open=False):
                    out_sources_registry = gr.Dataframe(label="Sources", interactive=False)
                
                # HANDLER
                def run_contextual_sizing(company, country, year, additional):
                    if not company.strip():
                        return (
                            "<div style='color:#FF5252; padding:20px;'>⚠️ Veuillez entrer un nom d'entreprise.</div>",
                            "", "", None, "", "", "", "", "", "", None, None
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
                            f"<div style='color:#FF5252; padding:20px;'>❌ Erreur : {error_msg}</div>",
                            "", "", None, "", "", "", "", "", "", None, None
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
                        {"<div style='color: #FFAB00; margin-top: 10px;'>⚠️ Infos manquantes: " + ', '.join(ctx.get('missing_info', [])) + "</div>" if ctx.get('missing_info') else ""}
                    </div>
                    """
                    
                    # 2. MARKET DEFINITION
                    mkt = analysis.get("market_definition", {})
                    local_adapt = mkt.get("local_adaptations", {})
                    excluded = mkt.get("excluded_segments", [])
                    
                    mkt_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="font-weight: bold; color: #0091DA; font-size: 1.1em; margin-bottom: 10px;">📍 {mkt.get('market_name', 'N/A')}</div>
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
                    
                    # 3. FACTS TABLE
                    facts_data = analysis.get("facts_used", [])
                    df_facts = pd.DataFrame(facts_data) if facts_data else pd.DataFrame()
                    
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
                    
                    # 6. VALIDATION TABLE
                    val = analysis.get("validation", {})
                    checks = val.get("sanity_checks", [])
                    df_validation = pd.DataFrame(checks) if checks else pd.DataFrame()
                    
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
                    
                    # 9. SOURCES TABLE
                    sources = analysis.get("sources_registry", [])
                    df_sources = pd.DataFrame(sources) if sources else pd.DataFrame()
                    
                    return (
                        ctx_html,
                        mkt_html,
                        df_facts,
                        eu_html,
                        ap_html,
                        uv_html,
                        ar_html,
                        calc_html,
                        final_html,
                        rel_html,
                        df_validation,
                        df_sources
                    )
                
                btn_run_sizing.click(
                    run_contextual_sizing,
                    inputs=[ctx_company, ctx_country, ctx_year, ctx_additional],
                    outputs=[
                        out_context_lock,
                        out_market_definition,
                        out_facts_local,
                        out_economic_unit,
                        out_addressable_pop,
                        out_unit_value,
                        out_adoption_rate,
                        out_calculation,
                        out_final_result,
                        out_reliability,
                        out_validation,
                        out_sources_registry
                    ]
                )

            # ─── ONGLET 2 : SEGMENTATION DES ENTREPRISES CONCURRENTES ───
            with gr.Tab("🎯 Segmentation Entreprises"):
                gr.Markdown("""
                ### 🎯 Segmentation des Entreprises Concurrentes
                
                > **Méthodologie** : Segmenter les entreprises qui CAPTENT la valeur du marché (pas les clients), 
                > en s'appuyant sur les résultats du Market Sizing contextuel.
                > Chaque segment = un sous-espace économique + logique de revenus distincte + poids économique différenciable.
                """)
                
                # SECTION 1: VERROUILLAGE DU CONTEXTE + MARKET SIZING
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("##### 1️⃣ Contexte & Résultats du Market Sizing")
                        with gr.Row():
                            seg_company = gr.Textbox(
                                label="🏢 Entreprise de Référence",
                                placeholder="ex: Doctolib, Alan, Qonto...",
                                value=""
                            )
                            seg_country = gr.Dropdown(
                                choices=["France", "Allemagne", "Pologne", "Espagne", "Italie", "UK", "USA"],
                                label="🌍 Pays / Zone",
                                value="France",
                                allow_custom_value=True
                            )
                        with gr.Row():
                            seg_offerings = gr.Textbox(
                                label="📦 Offre / Périmètre Fonctionnel",
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
                            label="📊 Résultats du Market Sizing (OBLIGATOIRE)",
                            placeholder="Collez ici les résultats du Market Sizing contextuel : définition du marché, unités économiques, ordres de grandeur, hypothèses structurantes...",
                            lines=5,
                            value=""
                        )
                        btn_run_segmentation = gr.Button("🚀 Segmenter les Entreprises du Marché", variant="primary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ##### ⚠️ ATTENTION
                        On segmente les **ENTREPRISES** qui captent la valeur, 
                        **pas les clients**.
                        
                        ##### 📋 Cette analyse va produire :
                        - ✅ Logique de segmentation retenue
                        - ✅ 4-8 segments d'entreprises
                        - ✅ Lien chiffré avec le sizing
                        - ✅ Positionnement de l'entreprise
                        - ✅ Carte du marché par acteurs
                        - ✅ Fiabilité & limites
                        """)
                
                # SECTION 2: CONTEXTE VERROUILLÉ
                with gr.Accordion("📌 1. Contexte & Market Sizing Utilisé", open=True):
                    out_seg_context = gr.HTML()
                
                # SECTION 3: LOGIQUE DE SEGMENTATION
                with gr.Accordion("📐 2. Logique de Segmentation Retenue", open=True):
                    out_seg_logic = gr.HTML()
                    out_seg_axes = gr.Dataframe(label="Axes Utilisés vs Rejetés", interactive=False)
                
                # SECTION 4: SEGMENTS D'ENTREPRISES
                gr.Markdown("### 🏢 3. Segments d'Entreprises (4-8 max)")
                out_seg_segments = gr.Dataframe(label="Types d'Entreprises Concurrentes", interactive=False, wrap=True)
                
                # SECTION 5: DISTRIBUTION DE VALEUR
                with gr.Accordion("💰 4. Distribution de la Valeur du Marché", open=True):
                    with gr.Row():
                        out_seg_pie = gr.Plot(label="Répartition par Type d'Acteurs")
                        out_seg_bubble = gr.Plot(label="Carte du Marché (Intégration × Valeur)")
                    out_seg_value_analysis = gr.HTML()
                
                # SECTION 6: POSITIONNEMENT ENTREPRISE
                with gr.Accordion("🎯 5. Positionnement de l'Entreprise de Référence", open=True):
                    with gr.Row():
                        out_seg_core = gr.HTML(label="Segments Cœur de Marché")
                        out_seg_adjacent = gr.HTML(label="Adjacents Crédibles")
                        out_seg_out_of_scope = gr.HTML(label="Hors Scope Réaliste")
                
                # SECTION 7: FIABILITÉ
                with gr.Accordion("🔍 6. Fiabilité & Limites", open=False):
                    out_seg_reliability = gr.HTML()
                    with gr.Row():
                        out_seg_sizing_facts = gr.Dataframe(label="Facts du Sizing Utilisés", interactive=False)
                        out_seg_hypotheses = gr.Dataframe(label="Nouvelles Hypothèses", interactive=False)
                
                # HANDLER
                def run_company_segmentation(company, offerings, country, year, market_sizing):
                    if not company.strip() or not offerings.strip():
                        return (
                            "<div style='color:#FF5252; padding:20px;'>⚠️ Veuillez entrer une entreprise et son offre.</div>",
                            "", None, None, None, None, "", "", "", "", "", None, None
                        )
                    
                    if not market_sizing.strip():
                        return (
                            "<div style='color:#FFAB00; padding:20px;'>⚠️ <b>Market Sizing manquant.</b> Veuillez d'abord exécuter le module Market Sizing Contextuel et coller les résultats ici. La segmentation s'appuie sur ces données.</div>",
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
                            f"<div style='color:#FF5252; padding:20px;'>❌ Erreur : {error_msg}</div>",
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
                    
                    # 2. SEGMENTATION LOGIC
                    logic = analysis.get("segmentation_logic", {})
                    primary = logic.get("primary_axis", {})
                    secondary = logic.get("secondary_axes", [])
                    rejected = logic.get("rejected_axes", [])
                    
                    logic_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px;">
                        <div style="font-weight: bold; color: #0091DA; font-size: 1.1em; margin-bottom: 15px;">🎯 Axe Principal de Segmentation</div>
                        <div style="background: rgba(0,145,218,0.15); padding: 15px; border-radius: 8px; border-left: 3px solid #0091DA;">
                            <div style="font-size: 1.1em; font-weight: bold;">{primary.get('axis_name', 'N/A')}</div>
                            <div style="opacity: 0.8; margin-top: 5px;">Type: <code>{primary.get('axis_type', 'N/A')}</code></div>
                            <div style="margin-top: 10px;"><b>Justification:</b> {primary.get('justification', 'N/A')}</div>
                            <div style="margin-top: 5px; color: #00C853;"><b>Lien avec le sizing:</b> {primary.get('link_to_sizing', 'N/A')}</div>
                        </div>
                    </div>
                    """
                    
                    # Axes table (secondary + rejected)
                    axes_for_df = []
                    for ax in secondary:
                        axes_for_df.append({
                            "Axe": ax.get("axis_name", ""),
                            "Type": ax.get("axis_type", ""),
                            "Statut": "✅ Secondaire",
                            "Justification/Raison": ax.get("relevance", "")
                        })
                    for ax in rejected:
                        axes_for_df.append({
                            "Axe": ax.get("axis_name", ""),
                            "Type": "-",
                            "Statut": "❌ Rejeté",
                            "Justification/Raison": ax.get("reason", "")
                        })
                    df_axes = pd.DataFrame(axes_for_df) if axes_for_df else pd.DataFrame()
                    
                    # 3. COMPANY SEGMENTS TABLE
                    segments = analysis.get("company_segments", [])
                    seg_for_df = []
                    for seg in segments:
                        mkt_share = seg.get("market_share_captured", {})
                        seg_for_df.append({
                            "ID": seg.get("segment_id", ""),
                            "Type d'Entreprise": seg.get("segment_name", ""),
                            "Logique de Valeur": seg.get("value_creation_logic", "")[:60] + "..." if len(seg.get("value_creation_logic", "")) > 60 else seg.get("value_creation_logic", ""),
                            "Unité Éco": seg.get("target_economic_unit", ""),
                            "Modèle Revenus": seg.get("revenue_model", ""),
                            "Prix": seg.get("pricing_position", ""),
                            "Valeur Captée (M€)": f"{mkt_share.get('value', 0)/1e6:.1f}" if mkt_share.get('value') else "N/A",
                            "Part Marché (%)": mkt_share.get("percentage_of_total", 0),
                            "Acteurs Représentatifs": ", ".join(seg.get("representative_players", [])[:3])
                        })
                    df_segments = pd.DataFrame(seg_for_df) if seg_for_df else pd.DataFrame()
                    
                    # 4. VISUALIZATIONS
                    import plotly.graph_objects as go
                    import plotly.express as px
                    
                    # Pie chart: Market share by segment
                    if segments:
                        seg_names = [s.get("segment_name", s.get("segment_id")) for s in segments]
                        seg_values = [s.get("market_share_captured", {}).get("percentage_of_total", 0) for s in segments]
                        
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=seg_names,
                            values=seg_values,
                            hole=0.4,
                            textinfo='label+percent',
                            marker=dict(colors=px.colors.qualitative.Set2)
                        )])
                        fig_pie.update_layout(
                            title="Répartition du Marché par Type d'Acteurs",
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white")
                        )
                    else:
                        fig_pie = go.Figure()
                        fig_pie.update_layout(title="Pas de données disponibles")
                    
                    # Bubble chart: Integration × Value
                    viz = analysis.get("visualizations", {})
                    market_map = viz.get("market_map", {})
                    
                    if market_map.get("data"):
                        fig_bubble = go.Figure()
                        for pt in market_map["data"]:
                            seg_name = next((s.get("segment_name", pt["segment"]) for s in segments if s.get("segment_id") == pt["segment"]), pt["segment"])
                            fig_bubble.add_trace(go.Scatter(
                                x=[pt.get("x", 0)],
                                y=[pt.get("y", 0)],
                                mode='markers+text',
                                marker=dict(size=pt.get("size", 20) * 2, opacity=0.7),
                                text=[seg_name],
                                textposition="top center",
                                name=seg_name
                            ))
                        fig_bubble.update_layout(
                            title=f"Carte du Marché: {market_map.get('x_axis', 'X')} × {market_map.get('y_axis', 'Y')}",
                            xaxis_title=market_map.get("x_axis", "Degré d'intégration"),
                            yaxis_title=market_map.get("y_axis", "Valeur captée"),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white"),
                            showlegend=False
                        )
                    else:
                        fig_bubble = go.Figure()
                        fig_bubble.update_layout(title="Pas de données de carte disponibles")
                    
                    # Value distribution analysis
                    dist = analysis.get("market_value_distribution", {})
                    value_html = f"""
                    <div style="background: #1E1E1E; padding: 20px; border-radius: 10px; margin-top: 15px;">
                        <div style="font-weight: bold; margin-bottom: 10px;">📈 Analyse de Concentration</div>
                        <div style="margin-bottom: 10px;">{dist.get('concentration_analysis', 'N/A')}</div>
                        <div style="color: #0091DA;"><b>Tendance de Migration de Valeur:</b> {dist.get('value_migration_trends', 'N/A')}</div>
                    </div>
                    """
                    
                    # 5. COMPANY POSITIONING
                    pos = analysis.get("reference_company_positioning", {})
                    
                    # Core segments
                    core_ids = pos.get("core_market_segments", [])
                    current = pos.get("current_segments", [])
                    core_html = "<div style='background: rgba(0,145,218,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #0091DA;'><div style='font-weight: bold; margin-bottom: 10px;'>🎯 Cœur de Marché</div>"
                    for c in current:
                        if c.get("segment_id") in core_ids:
                            seg_name = next((s.get("segment_name", c.get("segment_id")) for s in segments if s.get("segment_id") == c.get("segment_id")), c.get("segment_id"))
                            core_html += f"<div style='padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border-radius: 4px;'><b>{seg_name}</b><br><span style='opacity: 0.8;'>Présence: {c.get('presence_level', 'N/A')} | Part: ~{c.get('estimated_share_in_segment', 0)}%</span></div>"
                    core_html += "</div>"
                    
                    # Adjacent segments
                    adjacent = pos.get("credible_adjacent_segments", [])
                    adj_html = "<div style='background: rgba(0,200,83,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #00C853;'><div style='font-weight: bold; margin-bottom: 10px;'>🚀 Adjacents Crédibles</div>"
                    for a in adjacent:
                        seg_name = next((s.get("segment_name", a.get("segment_id")) for s in segments if s.get("segment_id") == a.get("segment_id")), a.get("segment_id"))
                        adj_html += f"<div style='padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border-radius: 4px;'><b>{seg_name}</b><br><span style='opacity: 0.8;'>Faisabilité: {a.get('expansion_feasibility', 'N/A')}</span><br><i>{a.get('strategic_rationale', '')}</i></div>"
                    adj_html += "</div>"
                    
                    # Out of scope
                    oos = pos.get("out_of_scope_segments", [])
                    oos_html = "<div style='background: rgba(255,82,82,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #FF5252;'><div style='font-weight: bold; margin-bottom: 10px;'>❌ Hors Scope Réaliste</div>"
                    for o in oos:
                        seg_name = next((s.get("segment_name", o.get("segment_id")) for s in segments if s.get("segment_id") == o.get("segment_id")), o.get("segment_id"))
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
                            <b>⚠️ Limitations:</b> {', '.join(rel.get('key_limitations', []))}
                        </div>
                    </div>
                    """
                    
                    # 7. FACTS & HYPOTHESES TABLES
                    fh = analysis.get("facts_and_hypotheses", {})
                    df_sizing_facts = pd.DataFrame(fh.get("sizing_facts_used", [])) if fh.get("sizing_facts_used") else pd.DataFrame()
                    df_hyps = pd.DataFrame(fh.get("new_hypotheses", [])) if fh.get("new_hypotheses") else pd.DataFrame()
                    
                    return (
                        ctx_html,
                        logic_html,
                        df_axes,
                        df_segments,
                        fig_pie,
                        fig_bubble,
                        value_html,
                        core_html,
                        adj_html,
                        oos_html,
                        rel_html,
                        df_sizing_facts,
                        df_hyps
                    )
                
                btn_run_segmentation.click(
                    run_company_segmentation,
                    inputs=[seg_company, seg_offerings, seg_country, seg_year, seg_market_sizing],
                    outputs=[
                        out_seg_context,
                        out_seg_logic,
                        out_seg_axes,
                        out_seg_segments,
                        out_seg_pie,
                        out_seg_bubble,
                        out_seg_value_analysis,
                        out_seg_core,
                        out_seg_adjacent,
                        out_seg_out_of_scope,
                        out_seg_reliability,
                        out_seg_sizing_facts,
                        out_seg_hypotheses
                    ]
                )

            # ─── ONGLET 3 : ANALYSE CONCURRENTIELLE (REVAMPED) ───
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