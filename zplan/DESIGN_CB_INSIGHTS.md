# Design System : L'Expérience "CB Insights"

> **Philosophie :** "Insight First, Audit Ready". L'utilisateur doit être saisi par le résultat (Wow Effect), puis rassuré par la méthode (Trust Effect).

---

## 1. Le Nouveau Flux d'Entrée (The Scope Selector)

Au lieu d'un simple champ texte "Scope", nous structurons la demande pour guider l'utilisateur et le moteur.

**Composants UI (Haut de Page) :**
*   **Secteur / Industrie** (ex: "Cybersécurité", "Cosmétiques Bio")
*   **Zone Géographique** (ex: "Europe", "Global", "Île-de-France")
*   **Horizon Temporel** (ex: "2024", "2030")
*   **Devise** (ex: "EUR", "USD")

*➡️ Ces inputs sont concaténés pour former le `Scope` technique (ex: "Marché de la Cybersécurité en Europe à l'horizon 2024 en EUR").*

---

## 2. Le "Hero Insight" (Le Chiffre d'Or)

C'est la partie supérieure de l'écran de résultat. Elle met en avant **UNE seule vérité**, celle choisie par l'algorithme adaptatif.

**Structure Visuelle :**
*   **Gros Chiffre (72pt)** : Valeur retenue (ex: **12.5 Md€**).
*   ** Badge de Confiance** : "Confiance Élevée" (Vert) ou "Estimation Indicative" (Orange).
*   **Baseline** : "Marché adressable théorique (TAM) basé sur la triangulation."
*   **Contexte** : "Croissance estimée : +5.2% CAGR" (Si dispo).

*👉 UX : Pas de distraction. C'est le chiffre qu'on met dans le slide.*

---

## 3. La "Story of Truth" (La Preuve par 3)

Juste en dessous, on "déplie" le raisonnement. On ne montre plus 4 cartes identiques, mais un **Entonnoir de Validation**.

1.  **L'Approche Macro (Top-Down)** : "🔍 Vue d'hélicoptère (Gartner/IDC...)" -> Montre le potentiel théorique.
2.  **L'Approche Terrain (Bottom-Up)** : "🏭 Vue opérationnelle (Clients x Prix)" -> Montre la réalité du business.
3.  **L'Approche Supply (Concurrence)** : "⚔️ Vue concurrentielle (Somme des revenus)" -> Montre le marché déjà pris.

**Interactivité :**
*   Les cartes sont visuellement connectées.
*   Si une méthode est "Écartée", elle est grisée avec la raison explicite ("Données insuffisantes").
*   Au clic, on voit le détail du calcul.

---

## 4. Plan de Migration Technique

### Étape 1 : Refonte des Inputs (`kpmg_interface.py`)
Remplacer `scope_input` par 3 composants `gr.Dropdown` / `gr.Textbox`.

### Étape 2 : Design du Hero (`kpmg_interface.py`)
Créer un nouveau composant HTML/CSS `hero_insight_html` qui remplace l'ancien `decision_html`. Il doit être beaucoup plus "Marketing".

### Étape 3 : Storytelling Layout
Réorganiser les cartes existantes en une ligne horizontale "Step-by-Step" ou un accordéon, plutôt qu'une grille 2x2.

### Étape 4 : Connexion au Moteur
Assurer que le moteur reçoit bien le scope concaténé pour lancer Mistral.
