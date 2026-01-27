# Méthode d’Estimation Adaptative & UX Explicite

> **Intention :** Le chiffre final n’est pas unique, il est le résultat d’un chemin méthodologique visible. Le système choisit automatiquement le niveau de précision le plus pertinent selon la qualité des Facts disponibles.

---

## 1. Logique d'Estimation Adaptative (The Brain)

Le moteur `MarketEstimationEngine` n'est plus passif. Il évalue la robustesse de chaque méthode et élit une **"Méthode Active"**.

### Les 4 Niveaux de Précision

1.  **Niveau 1 : Macro (Top-Down)**
    *   *Méthode :* `TAM * SAM% * SOM%`
    *   *Condition :* Avoir au moins un TAM global.
    *   *Statut :* "Estimation théorique" (Faible précision).
    
2.  **Niveau 2 : Demande (Bottom-Up)**
    *   *Méthode :* `Volume Clients * Prix Moyen`
    *   *Condition :* Avoir des données tangibles sur les clients et le pricing.
    *   *Statut :* "Estimation volumétrique" (Précision moyenne).

3.  **Niveau 3 : Offre (Production)**
    *   *Méthode :* `Volume Prod * Valeur Unitaire`
    *   *Condition :* Avoir des données de production concurrentielle.
    *   *Statut :* "Estimation industrielle" (Précision moyenne).

4.  **Niveau 4 : Triangulation (Convergence)**
    *   *Méthode :* Moyenne pondérée des méthodes valides ci-dessus.
    *   *Condition :* Avoir au moins 2 méthodes valides avec un écart < 30%.
    *   *Statut :* "Estimation robuste" (Haute précision).

### Algorithme de Sélection
Le système parcourt les niveaux du 4 au 1. Le premier niveau qui remplit ses conditions de "Confiance High" devient le **Niveau Actif**.

---

## 2. Expérience Utilisateur (UX)

L'interface ne se contente pas d'afficher 4 cartes. Elle raconte l'histoire de la sélection.

### A. Visualisation Progressive
*   **Niveau Actif :** Affiché en pleine opacité, avec une bordure de validation (✅) et une couleur vibrante.
*   **Niveaux Inactifs :** Grisés (Opacité 0.6), sans bordure, pour montrer qu'ils ont été calculés mais écartés (soit par manque de données, soit car une meilleure méthode existe).

### B. Justification ("Pourquoi ce choix ?")
Chaque carte affiche un tag explicite :
*   `RETENU` : "Méthode la plus précise disponible."
*   `ÉCARTÉ` : "Données trop partielles" ou "Moins précis que la triangulation."

### C. Le Chiffre Final
Un encart "Résultat Retenu" synthétise le choix du système, accompagné de son :
*   **Niveau de Confiance** (ex: "Élevé - Triangulé")
*   **Sources Clés** (ex: "Basé sur Gartner + Analyse Bottom-Up")

---

## 3. Implémentation Technique

1.  **Engine Update (`market_estimation_engine.py`)** :
    *   Ajout de la méthode `determine_best_method()`.
    *   Retourne l'index de la méthode gagnante.

2.  **Interface Update (`kpmg_interface.py`)** :
    *   Modification du CSS des cartes (`card-panel`) pour gérer l'état "Active" vs "Inactive".
    *   Injection dynamique des styles (Opacité, Bordures) selon le résultat de l'Engine.
