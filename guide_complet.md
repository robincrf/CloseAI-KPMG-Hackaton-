# 🎯 Système RAG de Veille Stratégique KPMG

## 📋 Vue d'Ensemble

Ce projet implémente un système RAG (Retrieval-Augmented Generation) complet pour la veille stratégique, conçu selon les exigences du Hackathon KPMG Global Strategy Group.

### Objectifs du Système

✅ **Automatiser la veille concurrentielle** : Économie de 60-70% du temps des analystes
✅ **Fournir des insights en temps réel** : Surveillance continue des marchés
✅ **Garantir la traçabilité** : Chaque information est sourcée et datée
✅ **Analyser multi-sources** : SEC EDGAR, NewsAPI, yfinance, communiqués de presse

---

## 🏗️ Architecture du Système

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE COMPLET                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Sources] → [Loaders] → [Chunking] → [Embeddings]          │
│                              ↓                                │
│               [Pinecone Index + Namespaces]                  │
│                              ↓                                │
│       [Retriever] → [Prompt KPMG] → [Mistral] → [Réponse]   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Composants Clés

| Composant            | Technologie              | Justification                                     |
| -------------------- | ------------------------ | ------------------------------------------------- |
| **Vector DB**  | Pinecone                 | Scalabilité serverless, isolation par namespaces |
| **Embeddings** | Mistral-embed (1024 dim) | Modèle multilingue, gratuit                      |
| **LLM**        | Mistral Medium           | Raisonnement avancé, plan gratuit                |
| **Framework**  | LangChain                | Écosystème complet, LCEL                        |

---

## 📁 Structure des Namespaces Pinecone

Les données sont isolées dans 5 namespaces pour permettre des requêtes ciblées :

| Namespace             | Sources                         | Usage                                         |
| --------------------- | ------------------------------- | --------------------------------------------- |
| `financial_reports` | SEC EDGAR, rapports annuels     | Due diligence, analyse financière            |
| `news`              | NewsAPI, communiqués de presse | Veille actualités, détection d'événements |
| `startups`          | *(futur)* Crunchbase          | Analyse de l'écosystème innovation          |
| `macro_data`        | yfinance, données économiques | KPIs financiers, tendances de marché         |
| `social_signals`    | *(futur)* Reddit, Twitter     | Sentiment analysis, early signals             |

---

## 🚀 Installation & Configuration

### Prérequis

```bash
Python 3.10+
pip install -r requirements.txt
```

### Dépendances Principales

```
langchain==1.2.0
langchain-community
langchain-mistralai
langchain-pinecone
pinecone-client==3.0.0
yfinance
requests
python-dotenv
```

### Configuration `.env`

Créez un fichier `.env` à la racine avec vos clés API :

```bash
# Pinecone
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1  # ou votre région

# Mistral AI
MISTRAL_API_KEY=your_mistral_key_here

# NewsAPI (optionnel, 100 requêtes/jour gratuit)
NEWSAPI_KEY=your_newsapi_key_here

# SEC EDGAR (obligatoire)
SEC_USER_AGENT="VotreNom votre.email@example.com"
```

#### Obtention des Clés API

1. **Pinecone** : https://app.pinecone.io/ (tier gratuit disponible)
2. **Mistral** : https://console.mistral.ai/ (crédits gratuits)
3. **NewsAPI** : https://newsapi.org/register (100 req/jour gratuit)

---

## 📓 Utilisation des Notebooks

### Workflow Complet (40 jours)

#### **Phase 1 : Setup (Jours 1-5)**

**Notebook 1 : Configuration Pinecone**

```bash
python 01_pinecone_setup.py
```

**Résultat attendu** :

- ✅ Index `kpmg-veille` créé
- ✅ Dimension 1024 (Mistral-embed)
- ✅ Métrique cosine configurée
- ✅ Namespaces documentés

---

#### **Phase 2 : Ingestion (Jours 6-15)**

**Notebook 2 : Ingestion Multi-Sources**

```bash
python 02_multi_source_ingestion.py
```

**Sources chargées** :

- SEC EDGAR (exemple : Apple 10-K)
- NewsAPI (actualités tech/finance)
- Communiqués de presse (web scraping)
- yfinance (données financières)

**Fichier généré** : `ingested_documents.json`

---

#### **Phase 3 : Chunking & Embeddings (Jours 16-30)**

**Notebook 3 : Chunking Adaptatif**

```bash
python 03_chunking_embeddings.py
```

**Stratégies appliquées** :

- **Financial reports** : Chunks 800 chars, overlap 19%
- **News** : Chunks 500 chars, overlap 20%
- **HTML** : Découpe par balises (H1, H2, H3)

**Fichier généré** : `embedded_documents.json`

---

#### **Phase 4 : Indexation (Jours 31-35)**

**Notebook 4 : Indexation Pinecone**

```bash
python 04_pinecone_indexation.py
```

**Actions** :

- Upsert par batch (100 vecteurs)
- Isolation par namespace
- Validation post-indexation

---

#### **Phase 5 : RAG Query (Jours 36-40)**

**Notebook 5 : Requêtes RAG**

```bash
python 05_rag_query_prompt.py
```

**Fonctionnalités** :

- Requêtes ciblées par namespace
- Citations obligatoires
- Prompt KPMG optimisé
- IA explicable

---

## 🎯 Exemples d'Utilisation

### Requête Simple

```python
from 05_rag_query_prompt import query_veille

response = query_veille(
    question="Quelle est la capitalisation boursière d'Apple ?"
)
print(response)
```

### Requête Ciblée (Namespace)

```python
response = query_veille(
    question="Quelles sont les dernières actualités sur l'IA ?",
    namespace="news"
)
```

### Comparaison Multi-Namespaces

```python
from 05_rag_query_prompt import compare_namespaces

results = compare_namespaces(
    question="Quels sont les risques pour les entreprises tech ?",
    namespaces=["financial_reports", "news", "macro_data"]
)

for namespace, response in results.items():
    print(f"\n--- {namespace} ---")
    print(response)
```

---

## 🔍 Caractéristiques du Prompt KPMG

Le prompt est conçu selon les exigences du Hackathon :

### 1. **Citations Obligatoires**

Chaque information factuelle doit être citée au format :

```
[Source | Fiabilité | Date]

Exemple :
"Apple a généré 394 milliards de dollars de revenus en 2023 
[SEC Filing 10-K | ⭐⭐⭐ | 2024-01-15]"
```

### 2. **Échelle de Fiabilité**

- ⭐⭐⭐ : Source primaire (SEC, rapports officiels, yfinance)
- ⭐⭐ : Source secondaire fiable (NewsAPI, presse reconnue)
- ⭐ : Source tertiaire (blogs, réseaux sociaux)

### 3. **Gestion des Cas Limites**

- **Données manquantes** : Le système l'indique explicitement
- **Accès payant** : Précisé dans la réponse
- **Ambiguïté** : Demande de clarification automatique

### 4. **Format de Réponse**

- Prose fluide (pas de bullet points par défaut)
- Structure narrative logique
- Ton professionnel mais accessible

---

## 📊 Métriques de Validation (KPIs)

### Phase de Test

Pour valider votre système lors de la présentation KPMG, utilisez ces métriques :

#### 1. **Hit Rate (Taux de Réussite)**

```python
# Tester avec 50 questions pré-définies
# Vérifier si les top 5 documents contiennent la réponse
hit_rate = documents_pertinents / total_questions
# Objectif : > 75%
```

#### 2. **LLM as a Judge (Précision)**

```python
# Utiliser un LLM pour scorer la cohérence (0-1)
# "La réponse contredit-elle les sources ?"
# Objectif : > 0.85
```

#### 3. **Human in the Loop (Satisfaction)**

- Ajouter des boutons 👍👎 dans l'interface
- Objectif : > 80% de satisfaction

#### 4. **Temps de Réponse**

- Mesurer la latence moyenne
- Objectif : < 5 secondes

---

## 🎨 Interface Gradio (Optionnel)

Pour créer une démo visuelle :

```python
import gradio as gr
from 05_rag_query_prompt import query_veille

def chat_interface(message, history):
    return query_veille(message)

demo = gr.ChatInterface(
    fn=chat_interface,
    title="🎯 Veilleur Stratégique KPMG",
    description="Assistant RAG pour l'analyse de marché",
    examples=[
        "Quelle est la capitalisation d'Apple ?",
        "Dernières actualités sur la fintech",
        "Analyse SWOT du secteur tech"
    ]
)

demo.launch(share=True)  # Crée un lien public 72h
```

---

## 🔒 Sécurité & Conformité

### Points de Vigilance KPMG

1. **RGPD** : Les données clients ne doivent jamais être indexées dans Pinecone sans consentement
2. **Audit Trail** : Les logs d'ingestion (`ingestion_logs/`) permettent la traçabilité
3. **Anonymisation** : Les métadonnées sensibles doivent être filtrées
4. **Chiffrement** : Les clés API doivent rester dans `.env` (jamais dans Git)

### Fichier `.gitignore`

```
.env
*.json
ingestion_logs/
__pycache__/
*.pyc
```

---

## 🚀 Optimisations Futures

### Court Terme (3 mois)

- [ ] Intégration Crunchbase (namespace `startups`)
- [ ] Alertes temps réel (webhooks)
- [ ] Cache Redis pour embeddings fréquents
- [ ] Multi-requêtes (reformulation automatique)

### Moyen Terme (6 mois)

- [ ] Agent LangGraph (validation auto des sources)
- [ ] Firecrawl pour JavaScript rendering
- [ ] LangSmith pour observabilité
- [ ] APIs internes KPMG

### Long Terme (12 mois)

- [ ] Fine-tuning Mistral sur données KPMG
- [ ] Génération automatique de PowerPoint
- [ ] Analyse prédictive (ML)
- [ ] Plateforme SaaS

---

## 📚 Références Techniques

### Documentation Officielle

- **LangChain** : https://python.langchain.com/docs/
- **Pinecone** : https://docs.pinecone.io/
- **Mistral AI** : https://docs.mistral.ai/
- **yfinance** : https://pypi.org/project/yfinance/
- **NewsAPI** : https://newsapi.org/docs

### Articles Recommandés

- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/)
- [Prompt Engineering Mistral](https://docs.mistral.ai/guides/prompting_capabilities/)

---

## 🤝 Support & Questions

### Troubleshooting

**Erreur : "PINECONE_API_KEY manquante"**

- Vérifiez votre fichier `.env`
- Assurez-vous que `load_dotenv()` est appelé

**Erreur : "dimension mismatch"**

- Supprimez et recréez l'index (Notebook 1)
- Vérifiez que vous utilisez `mistral-embed` (dimension 1024)

**Erreur : "rate limit exceeded"**

- NewsAPI : Limitez à 100 requêtes/jour
- Pinecone : Ajoutez `time.sleep(0.1)` entre batches

### Logs

Consultez `ingestion_logs/ingestion.log` pour débugger l'ingestion.

---

## 🎯 Checklist Présentation KPMG

- [ ] Démo live du Notebook 5
- [ ] Montrer les citations avec sources
- [ ] Illustrer l'isolation des namespaces
- [ ] Présenter les métriques (Hit Rate, précision)
- [ ] Expliquer le ROI (60% de temps économisé)
- [ ] Roadmap 3-6-12 mois
- [ ] Q&A sur scalabilité et sécurité

---

## 📄 Licence

Projet académique - Hackathon KPMG 2024

---

**Créé avec ❤️ pour KPMG Global Strategy Group**
