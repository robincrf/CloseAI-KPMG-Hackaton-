
import gradio as gr
import analytics_viz

def launch_dashboard(rag_stream_function):
    """
    Lance le tableau de bord complet KPMG (Chat + Finance + Stratégie).
    
    Args:
        rag_stream_function: La fonction génératrice du notebook (stream_kpmg_response)
    """
    
    # Thème personnalisé KPMG Pro
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("Source Code Pro"), "ui-monospace", "Consolas", "monospace"],
    ).set(
        body_background_fill="#121212", # Darker background
        body_text_color="#E0E0E0",
        block_background_fill="#1E1E1E", # Card background
        block_border_width="1px",
        block_border_color="rgba(255, 255, 255, 0.1)",
        block_label_text_color="#0091DA", # Secondary Blue
        input_background_fill="#262626",
        button_primary_background_fill="#00338D", # KPMG Primary Blue
        button_primary_text_color="white",
        button_secondary_background_fill="#262626",
        button_secondary_text_color="#0091DA",
        button_secondary_border_color="#0091DA",
        border_color_primary="#00338D",
        slider_color="#0091DA"
    )

    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    body, gradio-app { font-family: 'Inter', sans-serif !important; }
    
    /* Header Styling */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem;
        background: linear-gradient(90deg, #00338D 0%, #001E55 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 51, 141, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: #0091DA;
        font-size: 1rem;
        font-weight: 500;
        margin-top: 0.2rem;
    }

    /* Cards */
    .card-panel {
        background: #1E1E1E !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        border-color: rgba(0, 145, 218, 0.3) !important;
    }

    /* Tabs Styling */
    .tabs { margin-top: 1rem; }
    button.selected {
        background-color: rgba(0, 51, 141, 0.1) !important;
        border-bottom: 2px solid #00338D !important;
        color: #0091DA !important;
    }
    
    /* Plotly Container */
    .plotly-container {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Markdown Insights */
    .insight-text {
        font-size: 0.9rem;
        padding: 0.8rem;
        background: rgba(0, 145, 218, 0.1);
        border-left: 3px solid #0091DA;
        border-radius: 4px;
        margin-top: 0.5rem;
        color: #e0e0e0;
    }
    .reliability-badge {
        font-size: 0.75rem;
        color: #9e9e9e;
        margin-top: 0.2rem;
        display: block;
        font-style: italic;
    }

    /* Footer Cleanup */
    footer { display: none !important; }
    """

    with gr.Blocks(title="KPMG Analytics Dashboard") as demo:
        
        # Professional Header
        gr.HTML("""
        <div class="header-container">
            <div>
                <div class="header-title">KPMG <span style="font-weight:400; opacity:0.8;">Global Strategy Group</span></div>
                <div class="header-subtitle">Strategic Intelligence & Financial Analytics Platform</div>
            </div>
            <div style="text-align:right; color: #0091DA; font-family: monospace; font-size: 0.9rem;">
                v2.4.0-kpmg-internal
            </div>
        </div>
        """)
        
        with gr.Tabs():
            # ─── ONGLET 1 : CHAT RAG ───
            with gr.Tab("💬 Strategic Assistant"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("### 🤖 Assistant IA\nPosez vos questions sur les documents ingérés (News, Rapports financiers, etc.)")
                        # Image removed to prevent 403 errors (Wikimedia block)
                        # The HTML Header already provides sufficient branding.
                    
                    with gr.Column(scale=3):
                         gr.ChatInterface(
                            fn=rag_stream_function,
                            description="Assistant de Veille Stratégique alimenté par Mistral-Small.",
                            examples=["Actualités Apple", "Analyse SWOT Tesla", "Tendances IA 2024"]
                        )
            
            # ─── ONGLET 2 : FINANCE ───
            with gr.Tab("📈 Financial Dashboard"):
                with gr.Row():
                    gr.Markdown("### 📊 Market & Performance Analysis")
                
                # Zone de Configuration
                with gr.Accordion("Configuration du Dashboard", open=True):
                    with gr.Row():
                        ticker_input = gr.Textbox(label="Ticker (ex: AAPL, MSFT, TEF.PA)", value="AAPL")
                        period_input = gr.Dropdown(label="Période", choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="1y")
                    
                    indicators = gr.CheckboxGroup(
                        label="Indicateurs à afficher",
                        choices=[
                            "Cours de Bourse", 
                            "Revenus vs Net", 
                            "Free Cash Flow", 
                            "Marges", 
                            "Solvabilité (Dette)", 
                            "ROE / ROA", 
                            "Structure Bilan"
                        ],
                        value=["Cours de Bourse", "Revenus vs Net", "Marges"] # Défaut
                    )
                    btn_viz_fin = gr.Button("📊 Mettre à jour le Dashboard", variant="primary")

                # Grille d'affichage dynamique (6 slots)
                # Structure : Plot + Markdown d'insight en dessous
                with gr.Row():
                    with gr.Column(elem_classes=["card-panel"]):
                        p1 = gr.Plot(label="Slot 1")
                        m1 = gr.Markdown(visible=False, elem_classes=["insight-text"])
                    with gr.Column(elem_classes=["card-panel"]):
                        p2 = gr.Plot(label="Slot 2")
                        m2 = gr.Markdown(visible=False, elem_classes=["insight-text"])
                with gr.Row():
                    with gr.Column(elem_classes=["card-panel"]):
                        p3 = gr.Plot(label="Slot 3")
                        m3 = gr.Markdown(visible=False, elem_classes=["insight-text"])
                    with gr.Column(elem_classes=["card-panel"]):
                        p4 = gr.Plot(label="Slot 4")
                        m4 = gr.Markdown(visible=False, elem_classes=["insight-text"])
                with gr.Row():
                    with gr.Column(elem_classes=["card-panel"]):
                        p5 = gr.Plot(label="Slot 5")
                        m5 = gr.Markdown(visible=False, elem_classes=["insight-text"])
                    with gr.Column(elem_classes=["card-panel"]):
                        p6 = gr.Plot(label="Slot 6")
                        m6 = gr.Markdown(visible=False, elem_classes=["insight-text"])

                # Logique de mise à jour dynamique
                def update_financial_dashboard(ticker, period, selected_indicators):
                    # outputs = [p1, m1, p2, m2, ..., p6, m6] => 12 sorties
                    
                    # On initialise tout à Hidden
                    outputs = []
                    for _ in range(6):
                        outputs.append(gr.update(visible=False)) # Plot
                        outputs.append(gr.update(visible=False)) # Markdown
                    
                    current_slot_idx = 0
                    
                    # Helper pour ajouter un slot
                    def add_slot(result_dict):
                        nonlocal current_slot_idx
                        if current_slot_idx < 6:
                            # Les indices dans outputs sont : 2*i pour Plot, 2*i+1 pour Markdown
                            plot_idx = 2 * current_slot_idx
                            md_idx = plot_idx + 1
                            
                            fig = result_dict.get("fig")
                            insight = result_dict.get("insight", "")
                            reliability = result_dict.get("reliability", "")
                            
                            # Improved Markdown HTML
                            md_content = f"""
                            <div style='display:flex; align-items:flex-start;'>
                                <div style='font-size:1.2rem; margin-right:8px;'>💡</div>
                                <div>
                                    <div style='font-weight:600; color:#e0e0e0;'>Insight Automatique</div>
                                    <div style='color:#b0bec5;'>{insight}</div>
                                    <div class='reliability-badge'>{reliability}</div>
                                </div>
                            </div>
                            """ if insight else ""
                            
                            outputs[plot_idx] = gr.update(value=fig, visible=True)
                            outputs[md_idx] = gr.update(value=md_content, visible=True)
                            
                            current_slot_idx += 1

                    # 1. Cours de Bourse
                    if "Cours de Bourse" in selected_indicators:
                        res = analytics_viz.plot_stock_history(ticker, period)
                        add_slot(res)

                    # 2. Revenus vs Net
                    if "Revenus vs Net" in selected_indicators:
                        res = analytics_viz.plot_financial_kpis(ticker)
                        add_slot(res)

                    # 3. FCF & Marges
                    if "Free Cash Flow" in selected_indicators or "Marges" in selected_indicators:
                        # Retourne une liste de dicts
                        results = analytics_viz.plot_advanced_financials(ticker)
                        # results[0] = FCF, results[1] = Marges
                        if "Free Cash Flow" in selected_indicators:
                            add_slot(results[0])
                        if "Marges" in selected_indicators:
                            add_slot(results[1])

                    # 4. Solvabilité
                    if "Solvabilité (Dette)" in selected_indicators:
                        res = analytics_viz.plot_solvency_ratios(ticker)
                        add_slot(res)
                    
                    # 5. ROE / ROA
                    if "ROE / ROA" in selected_indicators:
                        res = analytics_viz.plot_returns(ticker)
                        add_slot(res)
                        
                    # 6. Bilan
                    if "Structure Bilan" in selected_indicators:
                        res = analytics_viz.plot_balance_sheet_structure(ticker)
                        add_slot(res)

                    return outputs

                btn_viz_fin.click(
                    update_financial_dashboard, 
                    inputs=[ticker_input, period_input, indicators], 
                    outputs=[p1, m1, p2, m2, p3, m3, p4, m4, p5, m5, p6, m6]
                )

            # ─── ONGLET 3 : STRATÉGIE ───
            with gr.Tab("🧠 Strategic Analysis (AI)"):
                with gr.Row():
                     gr.Markdown("### ⚡ AI-Powered Strategy Matrices")

                # Zone de Configuration
                with gr.Accordion("Matrix Configuration", open=True):
                    with gr.Row():
                        company_input = gr.Textbox(label="Entreprise cible", value="Tesla", scale=3)
                        btn_strat = gr.Button("🚀 Generate Matrices", variant="primary", scale=1)
                
                with gr.Row():
                    with gr.Column(elem_classes=["card-panel"]):
                        plot_swot = gr.Plot(label="Matrice SWOT")
                
                with gr.Row():
                    with gr.Column(elem_classes=["card-panel"]):
                        plot_bcg = gr.Plot(label="Matrice BCG")
                    with gr.Column(elem_classes=["card-panel"]):
                        plot_pestel = gr.Plot(label="Radar PESTEL")
                    
                btn_strat.click(analytics_viz.generate_swot_matrix, company_input, plot_swot)
                btn_strat.click(analytics_viz.generate_bcg_matrix, company_input, plot_bcg)
                btn_strat.click(analytics_viz.generate_pestel_radar, company_input, plot_pestel)

    # Lancement avec les paramètres mis à jour
    demo.launch(share=True, theme=theme, css=custom_css)
