# 📘 Justifications Techniques & Méthodologiques

## Document de Référence pour le Hackathon KPMG

Ce document justifie **chaque décision technique** prise dans l'architecture du système RAG de veille stratégique, en s'appuyant sur :

- ✅ Vos notes de projet (KPMG v2.pdf, hackathon KPMG.pdf)
- ✅ Les documentations officielles (LangChain, Pinecone, Mistral)
- ✅ Les best practices RAG

---

## 🏗️ Architecture Globale

### Décision : Architecture RAG vs. Fine-Tuning

**Choix retenu** : RAG (Retrieval-Augmented Generation)

**Justification** :

1. **Selon vos notes (hackathon KPMG.pdf)** :

   > "L'objectif est de bâtir un modèle capable d'effectuer des recherches sur différents éléments pré-définis [...] Les résultats du modèle doivent indiquer précisément des sources fiables, récentes et de façons croisées."
   >
2. **Avantages du RAG pour KPMG** :

   - ✅ **Traçabilité** : Chaque réponse cite ses sources (exigence critique)
   - ✅ **Fraîcheur** : Mise à jour des données sans réentraînement
   - ✅ **Coût** : Pas de fine-tuning coûteux
   - ✅ **Explicabilité** : Chaîne de raisonnement visible
3. **Référence LangChain** :

   > "RAG is a technique for augmenting LLM knowledge with additional data. LLMs can reason about wide-ranging topics, but their knowledge is limited to the specific timeframe when they were trained. If you want to build AI applications that can reason about private data or data introduced after a model's cutoff date, you need to augment the knowledge of the model with the specific information it needs."
   >

   Source : https://python.langchain.com/docs/tutorials/rag/

---

## 🗄️ Vector Database : Pinecone

### Décision : Pinecone vs. Alternatives

**Choix retenu** : Pinecone Serverless

**Alternatives évaluées** :

- ❌ Chroma : Difficultés de compilation sur Mac 2012 (vos notes)
- ❌ FAISS : Pas de persistence cloud, difficile à scaler
- ✅ Pinecone : Cloud, serverless, namespaces natifs

**Justification** :

1. **Selon vos notes (KPMG v2.pdf)** :

   > "Le passage à Pinecone et Mistral AI est la meilleure stratégie pour vous : tout le travail lourd sera fait sur leurs serveurs, pas sur votre processeur de 2012."
   >
2. **Avantages techniques** :

   - **Serverless Spec** : Scalabilité automatique (crucial pour production KPMG)
   - **Namespaces** : Isolation logique des sources (financial_reports, news, etc.)
   - **Pas de gestion d'infrastructure** : Fonctionne même sur Mac 2012
3. **Référence Pinecone** :

   > "Namespaces provide a way to separate vectors in a single index. They enable multi-tenancy scenarios where each tenant has isolated data."
   >

   Source : https://docs.pinecone.io/docs/namespaces

---

## 🧠 Modèle LLM : Mistral Medium

### Décision : Mistral vs. OpenAI/Claude

**Choix retenu** : Mistral Medium (avec plan gratuit)

**Justification** :

1. **Contrainte budgétaire (vos notes)** :

   > "Modèle : mistral-medium, Plan : gratuit"
   >
2. **Performance Mistral** :

   - Multilingue natif (FR/EN crucial pour KPMG international)
   - Raisonnement comparable à GPT-3.5
   - Contexte window : 32k tokens ≈ **20 000 à 25 000 mots ≈ **40–50 pages de texte ( token ≈ **¾ de mot anglais**)****

   La *context window* inclut :

   1. **System prompt** (instructions globales)
   2. **Developer prompt** (règles RAG, format, contraintes)
   3. **User prompt** (la question)
   4. **Contexte RAG injecté** (chunks récupérés)
   5. **Historique de conversation**
   6. **Réponse générée par le modèle**
3. **Optimisation du prompting** :

   Selon vos notes (KPMG v2.pdf) :

   > "J'ai vu que selon le model certains typ de prompt son plus efficace XML t markdown top pour claude et openain [...] je veux essayer de prompter au llm sous forme de MD"
   >

   **Notre implémentation** : Prompt structuré en Markdown avec séparateurs visuels
4. **Référence Mistral** :

   > "Mistral Medium is ideal for language transformation tasks that require moderate complexity, such as customer support chatbots or document summarization."
   >

   Source : https://docs.mistral.ai/getting-started/models/

---

## 📊 Embeddings : Mistral-embed

### Décision : Mistral-embed (1024 dimensions)

**Choix retenu** : `mistral-embed`

**Alternatives évaluées** :

- OpenAI text-embedding-ada-002 (1536 dim) : Payant
- Sentence Transformers (384-768 dim) : Dimension plus faible

**Justification** :

1. **Cohérence avec le LLM** : Même fournisseur (Mistral)
2. **Dimension optimale** : 1024 est un bon compromis précision/coût
3. **Gratuit** : Compatible avec contraintes budgétaires
4. **Configuration Pinecone** :

   ```python
   pc.create_index(
       name="kpmg-veille",
       dimension=1024,  # Correspond à Mistral-embed
       metric="cosine"   # Standard pour similarité sémantique
   )
   ```
5. **Référence Mistral** :

   > "The Mistral Embeddings API offers cutting-edge, state-of-the-art embeddings for text, which can be used for many NLP tasks."
   >

   Source : https://docs.mistral.ai/capabilities/embeddings/

---

## ✂️ Stratégie de Chunking

### Décision : Chunking Adaptatif par Type de Document

**Choix retenu** : 3 stratégies selon le namespace

**Justification** :

1. **Selon vos notes (KPMG v2.pdf)** :

   > "Le Chunking est souvent l'étape la plus sous-estimée, mais c'est elle qui détermine si ton IA va répondre précisément ou si elle va 'noyer' l'information."
   >
2. **Stratégies implémentées** :

   | Type Document               | Chunk Size            | Overlap   | Justification                                        |
   | --------------------------- | --------------------- | --------- | ---------------------------------------------------- |
   | **Financial Reports** | 800 chars             | 150 (19%) | Balance contexte/précision pour chiffres financiers |
   | **News**              | 500 chars             | 100 (20%) | Articles courts, informations denses                 |
   | **HTML Structuré**   | Variable (par balise) | N/A       | Préserve la structure sémantique (H1, H2)          |
3. **Référence vos notes** :

   > "Petits chunks (200-500 caractères) : Idéal pour trouver une donnée précise (ex: un chiffre d'affaires, une date). [...] Gros chunks (1000-2000 caractères) : Idéal pour comprendre un raisonnement ou une analyse stratégique."
   >
4. **Code implémenté** :

   ```python
   # Pour les rapports financiers
   RecursiveCharacterTextSplitter(
       chunk_size=800,
       chunk_overlap=150,  # 19% overlap
       separators=["\n\n", "\n", ". ", " ", ""]
   )
   ```
5. **Référence LangChain** :

   > "The RecursiveCharacterTextSplitter takes a large text and splits it based on a specified chunk size. It does this by using a set of characters."
   >

   Source : https://python.langchain.com/docs/modules/data_connection/document_transformers/

---

## 🔍 Stratégie de Retrieval

### Décision : Retrieval par Namespace avec k=5

**Choix retenu** : Similarité cosinus, top 5 documents

**Justification** :

1. **K=5 optimal** :

   - Selon vos notes : "Don't send 20 relevant chunks of data to the AI. Send the top 3 most relevant chunks."
   - Notre compromis : 5 chunks pour équilibrer contexte et vitesse
2. **Filtrage par namespace** :

   ```python
   vectorstore = PineconeVectorStore(
       index_name="kpmg-veille",
       namespace="financial_reports"  # Ciblé
   )
   ```
3. **Avantages** :

   - Requêtes ciblées (ex: uniquement actualités)
   - Réduit le bruit (exigence KPMG v2.pdf)
   - Améliore la pertinence
4. **Référence Pinecone** :

   > "Namespaces enable you to partition vectors within an index. Queries and updates only affect one namespace."
   >

   Source : https://docs.pinecone.io/docs/namespaces

---

## 📝 Prompt Engineering KPMG

### Décision : Prompt Structuré avec Citations Obligatoires

**Choix retenu** : Template Markdown avec règles explicites

**Justification** :

1. **Exigences hackathon KPMG.pdf** :

   > "Les résultats du modèle doivent indiquer précisément des sources fiables, récentes et de façons croisées."
   >
2. **Format de citation implémenté** :

   ```
   [Source | Fiabilité | Date]

   Exemple :
   "Apple a généré 394 milliards de revenus en 2023 
   [SEC Filing 10-K | ⭐⭐⭐ | 2024-01-15]"
   ```
3. **Échelle de fiabilité** :

   - ⭐⭐⭐ : Source primaire (SEC, yfinance)
   - ⭐⭐ : Source secondaire (NewsAPI, presse)
   - ⭐ : Source tertiaire (blogs)
4. **Structure du prompt** :

   ```
   ━━━ RÈGLES DE CITATION ━━━
   [Instructions explicites]

   ━━━ CONTEXTE ━━━
   {retrieved_docs}

   ━━━ QUESTION ━━━
   {user_query}

   ━━━ INSTRUCTIONS RÉPONSE ━━━
   [Format, tone, cas limites]
   ```
5. **Référence Mistral** :

   > "We recommend using structured prompts with clear delimiters. This helps the model understand the task better."
   >

   Source : https://docs.mistral.ai/guides/prompting_capabilities/

---

## 🔄 Gestion des Sources

### Décision : Loaders Spécialisés par Type de Source

**Choix retenu** : 4 loaders différents

| Source                        | Loader             | Justification                                 |
| ----------------------------- | ------------------ | --------------------------------------------- |
| **SEC EDGAR**           | Requests + API SEC | Données structurées, headers obligatoires   |
| **NewsAPI**             | Requests API       | API REST standard, authentification par clé  |
| **Communiqués Presse** | WebBaseLoader      | Web scraping éthique avec rate limiting      |
| **yfinance**            | yfinance library   | Spécialisé pour données financières Yahoo |

**Justification détaillée** :

1. **SEC EDGAR** :

   - Selon vos notes : "La SEC bloque les requêtes sans User-Agent"
   - Implémentation :
     ```python
     headers = {"User-Agent": SEC_USER_AGENT}
     response = requests.get(url, headers=headers)
     ```
2. **WebBaseLoader pour communiqués** :

   - Selon vos notes (KPMG v2.pdf) :

     > "Le WebBaseLoader est un wrapper autour de Requests et BeautifulSoup"
     >
   - Avantages :

     - Extraction automatique du texte
     - Gestion des balises HTML
     - Métadonnées de source
3. **Référence LangChain** :

   > "Document loaders provide a standard interface for reading data from different sources into LangChain's Document format."
   >

   Source : https://python.langchain.com/docs/modules/data_connection/document_loaders/

---

## ⚡ Optimisations de Performance

### Décision : Traitement par Batch + Cache

**Choix retenu** : Batch de 50-100 documents

**Justification** :

1. **Selon vos notes (KPMG v2.pdf)** :

   > "If your RAG chatbot is slow [...] 2️⃣ Cache everything you can. Similar questions get asked all the time. Save the embeddings and responses."
   >
2. **Implémentation batch embeddings** :

   ```python
   def generate_embeddings_batch(documents, batch_size=50):
       for i in range(0, len(documents), batch_size):
           batch = documents[i:i+batch_size]
           texts = [doc.page_content for doc in batch]
           embeddings = embeddings_model.embed_documents(texts)
   ```
3. **Avantages** :

   - Réduit les appels API (limite rate limiting)
   - Améliore la vitesse (parallélisation)
   - Économise des tokens (plan gratuit Mistral)
4. **Rate limiting Pinecone** :

   ```python
   time.sleep(0.1)  # 10 req/sec max pour tier gratuit
   ```

---

## 📊 Métriques de Validation

### Décision : 4 KPIs Standards de l'Industrie

**Choix retenu** : Hit Rate, LLM Judge, Human Feedback, Latence

**Justification** :

1. **Selon vos notes (KPMG v2.pdf)** :

   > "Non-technical stakeholders don't care about embeddings. They want numbers."
   >
2. **Métriques implémentées** :

   | Métrique                | Objectif | Mesure                                   |
   | ------------------------ | -------- | ---------------------------------------- |
   | **Hit Rate**       | > 75%    | Top 5 docs contiennent la réponse       |
   | **LLM Judge**      | > 0.85   | GPT-4 évalue cohérence source/réponse |
   | **Human Feedback** | > 80%    | Boutons 👍👎 dans interface              |
   | **Latence**        | < 5s     | Temps de réponse end-to-end             |
3. **Référence vos notes** :

   > "I used GPT-4 to score if each answer contradicted the source docs. The scale I chose was 0-1. It gave an AVG of 0.85. Now I could say '85% accuracy' in meetings."
   >

---

## 🔒 Sécurité & Conformité

### Décision : Logs d'Audit + Métadonnées Traçables

**Choix retenu** : Système de logging centralisé

**Justification** :

1. **Selon vos notes (KPMG v2.pdf)** :

   > "Les journaux d'audit sont essentiels à la conformité et à la sécurité. Ils doivent enregistrer [...] les identifiants des utilisateurs, les horodatages, les modèles de requête, les documents récupérés et les réponses générées."
   >
2. **Implémentation** :

   ```python
   def log_ingestion(source: str, status: str, details: str):
       timestamp = datetime.now().isoformat()
       log_entry = f"[{timestamp}] {source} - {status} : {details}\n"
       with open("ingestion_logs/ingestion.log", "a") as f:
           f.write(log_entry)
   ```
3. **Métadonnées enrichies** :

   - Source exacte (URL, API, fichier)
   - Date de récupération
   - Namespace d'origine
   - Type de document
4. **Conformité RGPD** :

   - Pas de données personnelles dans Pinecone
   - Clés API dans .env (hors Git)
   - Logs avec timestamps pour audits

---

## 🎯 Gestion des Cas Limites (KPMG)

### Décision : Logique de Fallback Explicite

**Choix retenu** : Instructions dans le prompt pour gérer ambiguïtés

**Justification** :

1. **Exigence hackathon KPMG.pdf** :

   > "Si le modèle ne parvient pas à identifier clairement le secteur ou le nom de la cible il doit pouvoir demander des précisions pour affiner, corriger les résultats – par exemple en cas de deux sociétés homonymes ou de marchés proche"
   >
2. **Implémentation dans le prompt** :

   ```
   4. CAS LIMITES :
      - Si vous ne trouvez pas l'information : "Les données disponibles 
        ne permettent pas de répondre. Sources consultées : [liste]. 
        Je recommande [action]."
      - Si une entreprise est ambiguë : "J'ai identifié plusieurs 
        entreprises nommées [X]. Pouvez-vous préciser : secteur, 
        géographie, ou autre contexte ?"
   ```
3. **Gestion données payantes** :

   ```python
   if 'paywall' in doc.metadata:
       response += "\n⚠️  Cette information nécessite un accès payant."
   ```

---

## 📈 Roadmap & Extensibilité

### Décision : Architecture Modulaire pour Ajout Futur de Sources

**Choix retenu** : Design pattern "Plugin"

**Justification** :

1. **Selon vos notes (hackathon KPMG.pdf)** :

   > "L'objectif est de bâtir un modèle capable d'effectuer des recherches sur différents éléments pré-définis"
   >
2. **Architecture extensible** :

   ```python
   # Ajouter une nouvelle source = créer une fonction
   def load_crunchbase_data(company: str) -> List[Document]:
       # Implémentation
       pass

   # L'ajouter au pipeline
   all_documents["startups"].extend(load_crunchbase_data("Stripe"))
   ```
3. **Namespaces prévus** :

   - ✅ `financial_reports` (SEC)
   - ✅ `news` (NewsAPI, presse)
   - ✅ `macro_data` (yfinance)
   - 🔜 `startups` (Crunchbase)
   - 🔜 `social_signals` (Reddit, Twitter)
4. **Référence vos notes (KPMG v2.pdf)** :

   > "3 mois : Pilote avec 2 équipes KPMG. 6 mois : Productionnalisation complète + 10 secteurs verticaux"
   >

---

## 🎨 Choix UI : Gradio vs. Streamlit

### Décision : Gradio (Recommandé)

**Choix retenu** : Gradio ChatInterface

**Justification** :

1. **Selon votre code existant** :

   ```python
   demo = gr.ChatInterface(
       fn=chat_response,
       title="Veilleur stratégique KPMG",
       share=True  # Lien public 72h pour jury
   )
   ```
2. **Avantages Gradio** :

   - ✅ Démo instantanée avec `share=True`
   - ✅ Interface chat native
   - ✅ Intégrable dans systèmes KPMG (iframe)
   - ✅ Moins de code que Streamlit
3. **Référence Gradio** :

   > "ChatInterface is a high-level abstraction that allows you to create chatbot UIs with minimal code."
   >

   Source : https://www.gradio.app/docs/chatinterface

---

## 📚 Références Croisées

### Documentation Consultée

✅ **LangChain** :

- Document Loaders : https://python.langchain.com/docs/modules/data_connection/document_loaders/
- Text Splitters : https://python.langchain.com/docs/modules/data_connection/document_transformers/
- Vector Stores : https://python.langchain.com/docs/modules/data_connection/vectorstores/
- RAG Tutorial : https://python.langchain.com/docs/tutorials/rag/

✅ **Pinecone** :

- Upsert Data : https://docs.pinecone.io/docs/upsert-data
- Namespaces : https://docs.pinecone.io/docs/namespaces
- Python Client : https://docs.pinecone.io/docs/python-client

✅ **Mistral AI** :

- Models : https://docs.mistral.ai/getting-started/models/
- Embeddings : https://docs.mistral.ai/capabilities/embeddings/
- Prompting : https://docs.mistral.ai/guides/prompting_capabilities/

✅ **Vos Notes Projet** :

- hackathon KPMG (1).pdf : Exigences clients, cas d'usage
- KPMG v2 (1).pdf : Best practices RAG, chunking, métriques

---

## ✅ Checklist de Conformité KPMG

- [X] Citations obligatoires avec source, fiabilité, date
- [X] Gestion des cas limites (ambiguïté, données manquantes)
- [X] Isolation des sources par namespaces
- [X] Logs d'audit pour traçabilité
- [X] Réponses en prose (pas de bullet points par défaut)
- [X] Métriques de validation (Hit Rate, Précision, Satisfaction)
- [X] Architecture extensible (ajout de sources facilité)
- [X] Conformité RGPD (pas de données sensibles indexées)

---

**Conclusion** : Chaque choix technique de ce système est justifié par :

1. Les exigences explicites du Hackathon KPMG
2. Les best practices documentées
3. Les contraintes matérielles et budgétaires identifiées
4. L'état de l'art en RAG et veille stratégique

Cette architecture garantit un système **robuste, extensible et conforme** aux standards KPMG.
