# 📄 Azure Content Understanding — Document Analysis (Batch 1)

## Description

Ce projet teste les **analyseurs pré-construits d'Azure AI Content Understanding** sur un lot de 20 documents scannés (factures, devis, bons de commande…).

Chaque document est analysé puis enrichi avec :
- **Extraction structurée des champs** (émetteur, montant, date, lignes d'articles…)
- **Description globale générée par GPT-4.1** déployé sur la ressource Cognitive Services

## Architecture

```
├── docu_prebuilt_invoice.ipynb    # Notebook principal d'analyse
├── batch_1/
│   ├── batch1_1/                  # 20 images sources (factures scannées)
│   └── docu_results_batch1_1/     # Résultats JSON enrichis
│       ├── prebuilt-invoice/      # Résultats analyseur facture
│       ├── prebuilt-layout/       # Résultats analyseur layout
│       ├── prebuilt-read/         # Résultats analyseur OCR
│       ├── all_metrics.json       # Métriques agrégées
│       └── model_comparison_summary.json
```

## Services Azure utilisés

| Service | Usage |
|---------|-------|
| **Azure AI Content Understanding** | Extraction de champs structurés (facture, layout, OCR) |
| **GPT-4.1** (Cognitive Services) | Description globale de chaque document |
| **Azure AD** | Authentification (DefaultAzureCredential) |

## Pipeline

1. **Authentification** — Token Azure AD (cache automatique)
2. **Test** — Vérification des analyseurs disponibles sur 1 document
3. **Batch Submit** — Envoi asynchrone des 20 documents
4. **Batch Poll** — Récupération des résultats (polling)
5. **Enrichissement** — Extraction des valeurs de champs + description LLM
6. **Sauvegarde** — JSON enrichi par document dans `docu_results_batch1_1/`

## Format de sortie (JSON enrichi)

Chaque fichier JSON de résultat contient :
- La réponse complète de Content Understanding (champs, markdown, tables, pages)
- Un bloc `_extracted` ajouté avec :
  - `field_values` : dictionnaire `{nom_champ: valeur}` (récursif pour sous-objets/tableaux)
  - `description` : description globale du document en français (2-3 phrases)

## Prérequis

- Python 3.10+
- Packages : `requests`, `azure-identity`
- Accès Azure AD à une ressource Cognitive Services avec Content Understanding + GPT déployé

## Utilisation

```bash
pip install requests azure-identity
```

Ouvrir `docu_prebuilt_invoice.ipynb` et exécuter les cellules dans l'ordre.
