# Méthodologie d'Estimation Granulaire (Smart Estimation)

> **Philosophie : "Granularité > Source Unique"**
> Plutôt que de chercher un "chiffre magique", le moteur construit une estimation pièce par pièce en choisissant la meilleure stratégie mathématique selon la qualité des données disponibles.

---

## 1. Moteur de Décision Adaptatif
Le système ne se contente pas d'appliquer une seule formule. Pour chaque composante (Macro, Demande, Offre), il évalue plusieurs **Stratégies** possibles et retient celle qui offre le meilleur score de **Complétude** et de **Confiance**.

### Algorithme de Sélection ("Hero Metric")
Le chiffre final affiché est choisi selon la priorité suivante :
1.  **Triangulation** (Si au moins 2 méthodes convergent).
2.  **Methode Demande (Bottom-Up)** (Si données granulaires disponibles).
3.  **Methode Offre (Supply)** (Si données de production disponibles).
4.  **Methode Macro (Top-Down)** (Solution de repli).

---

## 2. Détail des Stratégies de Calcul

### A. Estimation Macro (Top-Down)
*Vise à cadrer le potentiel théorique maximal.*

| Stratégie | Formule | Cas d'usage |
| :--- | :--- | :--- |
| **Classique** | `TAM Global ($) × % SAM (Géographie/Segment)` | Marchés matures avec rapports existants (Gartner, etc.). |
| **Proxy Économique** | `PIB Cible × Ratio PIB du Secteur (%)` | Marchés émergents ou sans rapport spécifique. |

### B. Estimation par la Demande (Bottom-Up)
*Vise à mesurer la réalité terrain. C'est souvent l'estimation la plus robuste.*

| Stratégie | Formule | Cas d'usage |
| :--- | :--- | :--- |
| **Volume Standard** | `Nombre Clients Potentiels × Prix Moyen AnnueL` | B2B/B2C établi avec base clients identifiable. |
| **Micro-Niche** | `Pop. Cible × Taux Pénétration (Proxy) × Prix` | Segments innovants (ex: "Pop. Intolérante Gluten"). |

### C. Estimation par l'Offre (Supply-Side)
*Vise à mesurer le marché par ce qui est physiquement produit ou vendu.*

| Stratégie | Formule | Cas d'usage |
| :--- | :--- | :--- |
| **Production** | `Volume Produit (Unités) × Valeur Unitaire (€)` | Industries, Matières premières. |
| **Somme Concurrents** | `Σ(Revenus Leaders) / Part de Marché Estimée` | Marchés oligopolistiques où les acteurs sont publics. |

---

## 3. Gestion de l'Incertitude

Le système qualifie chaque donnée utilisée pour garantir la transparence :

*   <span style="color:#4CAF50">**HARD DATA**</span> : Donnée issue d'une source primaire (Bilan financier, Recensement INSEE).
*   <span style="color:#FF9800">**PROXY**</span> : Donnée dérivée d'un marché comparable (ex: "Taux de churn telecoms" appliqué aux assurances).
*   <span style="color:#F44336">**ESTIMATION**</span> : Hypothèse pure en l'absence de données.

> Si une méthode manque de données critiques (ex: Prix manquant), elle est automatiquement **disqualifiée** au profit d'une méthode complète.
