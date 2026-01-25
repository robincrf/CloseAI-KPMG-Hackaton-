# Plan d'Action : Enrichissement Massif de l'Estimation

> **Objectif :** Transformer le système actuel (qui génère 3 chiffres TAM/SAM/SOM) en un véritable moteur de recherche qui "moissonne" des centaines de points de données pour trianguler la vérité.

---

## Axe 1 : "Supply-Side" (Reconstitution par les concurrents)
*L'idée : Si on ne connait pas la taille du gâteau, on additionne les parts des convives.*

### 1.1 Découverte Automatique de Concurrents (Mistral + YFinance)
*   **Action :** Demander à Mistral non pas le TAM, mais *"Quels sont les 5 principaux concurrents cotés en bourse pour [Scope] ?"* et leurs tickers (ex: SAP, ORACLE, SAGE).
*   **Enrichissement :** Le système itère ensuite sur YF pour récupérer le **Chiffre d'Affaires (Revenue)** exact de chacun.
*   **Calcul Dérivé (Fact) :**
    *   `Somme des Revenus Concurrents du Top 5` = `Plancher de marché (Supply Floor)`.
    *   Estimation : `Plancher / (Somme des Parts de Marché estimées)` = `TAM Total`.

### 1.2 Analyse des Marges & Prix (Signals)
*   **Action :** Récupérer la marge brute moyenne du secteur via YF.
*   **Usage :** Si on a une estimation par les coûts, on peut diviser par `(1 - Marge)` pour retrouver le Revenu Marché.

---

## Axe 2 : "Demand-Side" (Granularité Bottom-Up)
*L'idée : Ne pas deviner le marché, mais deviner ses composantes élémentaires.*

### 2.1 Segmentation Granulaire (Mistral)
*   **Action :** Au lieu de demander un "Nb Clients", demander une segmentation :
    *   *Segment A (Grands Comptes) :* Nombre X, Panier Y.
    *   *Segment B (PME) :* Nombre X, Panier Y.
*   **Stockage :** Créer des Facts pour chaque sous-segment (`segment_a_volume`, `segment_a_arpu`).
*   **Calcul :** `Somme (Si * Pi)` beaucoup plus robuste qu'une simple moyenne.

### 2.2 Proxies de Volume (Trafic, Employés...)
*   **Action :** Chercher des proxies. Ex: "Nombre d'employés dans le secteur Logistique en France" (Fact INSEE/Statista simulé par Mistral).
*   **Usage :** Ratio `Dépense Software par Employé` x `Nb Employés Total`.

---

## Axe 3 : Implémentation Technique (Roadmap)

### Étape A : Service "Competitor Scout"
Créer une méthode `find_competitors(ticker)` dans `StrategicFactsService` qui renvoie une liste de tickers concurrents.

### Étape B : Boucle d'Ingestion Financière
Modifier `load_initial_state` pour qu'il s'exécute en boucle sur les concurrents trouvés :
```python
concurrents = service.find_competitors("AAPL") # -> ["MSFT", "GOOG", ...]
for c in concurrents:
    facts_manager.ingest_financials(c)
```
-> Le tableau de Facts passera de 10 lignes à **50+ lignes**.

### Étape C : Mise à jour de l'Engine (Supply Component)
Mettre à jour `get_supply_estimation` pour qu'il sache :
1. Filtrer les facts de type "Revenu".
2. Les additionner.
3. Produire une estimation "Somme des Concurrents".

---

## Résultat Attendu
Le module d'estimation affichera alors :
*   **Niveau 3 (Offre)** basé sur *"La somme vérifiée des revenus de 5 concurrents majeurs (12 Md€) + Long tail estimée (3 Md€)"*.
*   Ce chiffre sera **High Confidence** car basé sur des rapports financiers audités (YF), et non sur une hallucination LLM.
