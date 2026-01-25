# Documentation Technique : Architecture "FACTS-FIRST"

> **Principe clé :** Aucune donnée n'est codée en dur. Tout chiffre utilisé pour un calcul ou une analyse provient d'un réservoir unique et auditable appelé le "Facts Manager".

---

## 1. Le Concept de FACT

Un **Fact** est l'unité atomique d'information dans le système. Ce n'est pas juste un chiffre, c'est un objet structuré qui porte sa propre traçabilité.

### Structure d'un Fact (JSON)

```json
{
    "id": "gen_tam_1706182939",           // Identifiant unique
    "category": "market_estimation",      // Catégorie (market, finance, strategy...)
    "key": "tam_global_market",           // Clé fonctionnelle (utilisée par l'engine)
    "value": 5000000000,                  // La donnée brute (numérique ou textuelle)
    "unit": "EUR",                        // Unité
    "source": "Gartner 2023",             // Origine déclarée
    "source_type": "Secondaire (Rapport)",// Typologie (Primaire, Secondaire, Estimation)
    "retrieval_method": "Direct",         // Méthode (Extraction, Proxy, Calcul Ferm)
    "confidence": "medium",               // Score de confiance (low/medium/high)
    "notes": "Marché global des ERP..."   // Contexte
}
```

---

## 2. Cycle de Vie d'une Session

Pour garantir que les données sont toujours fraîches et pertinentes par rapport au contexte du client, le système suit ce cycle strict à chaque démarrage :

### A. Nettoyage (Reset)
À chaque lancement de l'interface (`load_initial_state`), le système :
1. **Vide entièrement** le `FactsManager` (mémoire + fichier JSON).
2. Garantit qu'aucun résidu d'une session précédente ne pollue l'analyse.

### B. Génération Dynamique (Ingestion)
Le système reconstruit alors les Facts "à la volée" via plusieurs agents :

1. **Strategic Agent (Mistral)** : 
   - Reçoit le scope (ex: "Logiciels ERP PME France").
   - Estime le TAM/SAM/SOM via des modèles de raisonnement (Fermi).
   - Génère des Facts avec sources simulées ou réelles.
   
2. **Financial Agent (Yahoo Finance)** :
   - Récupère les données boursières réelles (Revenus, Marge, Employés).
   - Crée des Facts certifiés "Donnée Réelle".

### C. Exécution (Engine)
Le moteur de calcul (`market_estimation_engine.py`) n'a pas de paramètres. Il :
- Interroge le `FactsManager` ("Donne-moi le TAM").
- Effectue les calculs (Top-Down, Bottom-Up).
- **Trace** quels Facts ont été utilisés pour chaque résultat.

### D. Audit (Restitution)
L'interface affiche :
- Le résultat du calcul.
- **Le Tableau de Centralisation** : Une vue directe sur la base de Facts, permettant de valider "Qui a dit ça ?" pour chaque chiffre.

---

## 3. Avantages de l'Approche

| Caractéristique | Bénéfice pour KPMG |
| :--- | :--- |
| **Traçabilité** | Chaque chiffre affiché à l'écran a une source explicite (Source + Type). |
| **Flexibilité** | On peut corriger une source dans le JSON, tout le Waterfall se recalcule. |
| **Robustesse** | Si une donnée manque (ex: PRIX), l'Engine le détecte et propose une stratégie de palliation, sans planter. |
| **Auditabilité** | Le fichier `market_sizing_facts.json` peut être exporté et joint au rapport final comme preuve de rigueur. |

---

## 4. Composants Techniques

*   `facts_manager.py` : Le gardien de la base de données (CRUD).
*   `market_estimation_engine.py` : Le cerveau qui consomme les facts pour produire des KPIs.
*   `strategic_facts_service.py` : L'agent IA qui "crée" de la donnée intelligente (estimations) quand elle manque.
*   `kpmg_interface.py` : L'orchestrateur qui déclenche le cycle Reset -> Generate -> Display.
