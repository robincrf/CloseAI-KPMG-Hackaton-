Projet RAG - HACK KPMG
---

## À LIRE ABSOLUMENT (Avant toute modification)

Avant de modifier le code, vous devez impérativement prendre connaissance des ressources suivantes :

1.  **Documentation Interne :**
    * `guide_complet.md` : Guide technique et structure du projet.
    * `justifications_tech.md` : Choix technologiques et architecture.
2.  **Contexte & Historique :**
    * Consulter la [Discussion avec Claude](https://claude.ai/share/7017a207-54c0-4c9d-9b14-e580829f64a0) pour comprendre la genèse du projet.
    * *Note importante :* Des modifications ont été apportées après le premier message de Claude. **Veuillez lire l'intégralité de la discussion.**

---

## Utilisation avec un LLM

Si vous utilisez une IA (ChatGPT, Claude, etc.) pour vous aider dans le développement, vous **devez** impérativement lui fournir les éléments suivants dans son contexte pour éviter les erreurs :

* Le fichier `main.ipynb` (le cœur du projet).
* Le fichier `requirements.txt` (pour l'environnement).
* Les deux documents Markdown (`guide_complet.md` et `justifications_tech.md`).

---

##  Consignes de Collaboration

Pour maintenir un historique propre et éviter les conflits sur la branche principale :

* **Création de branche :** Créez systématiquement votre propre branche avant de travailler.
    ```bash
    git checkout -b nom-de-votre-branche
    ```
* **Commits détaillés :** Détaillez précisément vos modifications dans vos messages de commit pour que l'équipe puisse suivre l'évolution.
    * *Exemple :* `git commit -m "Fix: Correction de la fonction de vectorisation dans main.ipynb"`

---

## 🚀 Quick Start (Facts-First)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start (Facts-First)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Dashboard**
   ```bash
   python main.py
   ```
   - Open the displayed URL (e.g., http://127.0.0.1:7860).

3. **Analysis Workflow (All-in-One)**
   - Go to the **"🎯 Estimation du Marché"** tab.
   - Enter a **Ticker** (e.g., `TSLA` for Tesla, `LVMUY` for LVMH).
   - Click **"📂 Charger Facts & Stratégie"**.
     - 🔄 **Auto-Sync**: The app will automatically fetch real-time financials and generate the strategic analysis (SWOT/BCG) via AI.
   - Once loaded, explore the Context Visualizations.
   - Click **"🔄 Recalculer"** to triangulate the market size against the real revenue.

*(Optional)* You can still use the CLI script for batch processing:
```bash
python scripts/sync_facts.py --company "Tesla" --ticker "TSLA"
```

## 🏗️ Architecture

- **`facts_manager.py`**: Central source of truth. Manages `market_sizing_facts.json`.
- **`facts_service.py`**: Fetches raw financial data (yfinance).
- **`strategic_facts_service.py`**: Generates SWOT/BCG/PESTEL via LLM (Mistral).
- **`analytics_viz.py`**: Generates Plotly charts from the facts.
- **`kpmg_interface.py`**: The Gradio UI.

## 🔑 Key Features
- **Data-Driven**: UI components are powered by structured facts, not hardcoded values.
- **Real-Time Context**: Integrates live market data for validation.
- **Strategic Triangulation**: Combines Top-Down, Bottom-Up, and Comparables.

---

##  Aperçu du Repository

* `main.ipynb` : Notebook principal contenant la logique RAG.
* `UI/` : Dossier contenant les captures d'écran de l'interface.
* `test.ipynb` / `test2.ipynb` : Notebooks de test et d'expérimentation.
* `*.md` : Documentation technique et guides.
