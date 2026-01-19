sour# Projet RAG - HACK KPMG
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

##  Aperçu du Repository

* `main.ipynb` : Notebook principal contenant la logique RAG.
* `UI/` : Dossier contenant les captures d'écran de l'interface.
* `test.ipynb` / `test2.ipynb` : Notebooks de test et d'expérimentation.
* `*.md` : Documentation technique et guides.
