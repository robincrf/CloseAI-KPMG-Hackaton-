# Plan d'Implémentation : Visualisation et Outils d'Analyse

Ce plan détaille l'ajout de capacités de visualisation de données (graphiques financiers) et de synthèse stratégique (matrices SWOT/BCG) à l'application existante.

## 1. Objectifs
- Ajouter des graphiques financiers interactifs (Cours de bourse, KPIs).
- Générer des matrices stratégiques (SWOT, BCG) via LLM.
- Intégrer le tout dans une interface Gradio à onglets.

## 2. Modifications Techniques

### Dépendances
- Ajout de `plotly` et `pandas` pour la manipulation et visualisation de données.

### Nouveau Module : `analytics_viz.py`
Ce fichier contiendra toute la logique de génération de graphiques pour ne pas alourdir le notebook principal.

#### Fonctionnalités Financières
- **Graphique Historique** : Courbe interactive du prix de l'action sur 1 an, 5 ans, etc.
- **KPIs** : Comparaison visuelle des revenus, bénéfices, marges.

#### Fonctionnalités Stratégiques (IA)
- **SWOT** : Prompt spécialisé pour extraire Forces/Faiblesses/Opportunités/Menaces en JSON, puis affichage graphique.
- **BCG** : Estimation du positionnement (Croissance vs Part de marché) pour visualiser les domaines d'activité stratégiques.

### Interface Utilisateur (Gradio)
Refonte de l'interface en 3 onglets :
1. **💬 Assistant** : Le chat RAG actuel.
2. **📈 Finance** : Tableau de bord avec inputs (Ticker) et graphiques Plotly.
3. **🧠 Stratégie** : Outils d'analyse avec inputs (Nom entreprise) et matrices.

## 3. Plan de Développement
1. Installation des dépendances.
2. Création de `analytics_viz.py`.
3. Implémentation des fonctions financières (YFinance + Plotly).
4. Implémentation des fonctions stratégiques (Mistral + Plotly).
5. Mise à jour de `main.ipynb` pour intégrer les onglets Gradio.
