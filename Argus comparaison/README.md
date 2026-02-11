# 📄 Azure Document Extraction — Batch 1 Analysis

Comparaison de **3 méthodes** d'extraction documentaire appliquées à un batch de **20 factures** (images JPG).

## 🏗️ Architecture du projet

```
docu_results_batch1_1/
├── README.md                        # Ce fichier
├── comparison_cu_vs_argus.ipynb     # Notebook de comparaison (3 méthodes)
├── .env                             # Credentials (non commité)
├── all_metrics.json                 # Métriques globales
├── model_comparison_summary.json    # Résumé de comparaison des modèles
├── prebuilt-invoice/                # Résultats Content Understanding (20 docs)
│   └── batch1-0001.json ... batch1-0020.json
├── prebuilt-layout/                 # Résultats Doc Intelligence layout (18 docs)
│   └── batch1-0001.json ... batch1-0018.json
├── prebuilt-read/                   # Résultats Doc Intelligence read (18 docs)
│   └── batch1-0001.json ... batch1-0018.json
├── argus-style-di/                  # Résultats ARGUS + Doc Intelligence OCR (20 docs)
│   └── batch1-0001.json ... batch1-0020.json
└── argus-style-mistral/             # Résultats ARGUS + Mistral Doc AI OCR (20 docs)
    └── batch1-0001.json ... batch1-0020.json
```

## 🔬 Méthodes comparées

| | Méthode 1 — Content Understanding | Méthode 2 — ARGUS + DocIntel | Méthode 3 — ARGUS + Mistral |
|---|---|---|---|
| **OCR** | `prebuilt-invoice` (API intégrée) | `prebuilt-layout` (Document Intelligence) | `mistral-document-ai-2505` (Mistral Doc AI) |
| **Extraction** | Modèle pré-entraîné (31 champs fixes) | GPT-5-chat (schéma personnalisable, 15 champs) | Mistral doc ai (schéma personnalisable, 15 champs) |
| **Approche** | Extraction directe en 1 appel | Pipeline OCR → LLM (2 étapes) | Pipeline OCR → LLM (2 étapes) |
| **Philosophie** | Schéma fixe Microsoft | Flexible, inspiré [ARGUS](https://github.com/Azure-Samples/ARGUS) | Flexible, inspiré [ARGUS](https://github.com/Azure-Samples/ARGUS) |

## 📊 Résultats — Synthèse

### Métriques agrégées (20 factures)

| Métrique | Content Understanding | ARGUS + DocIntel | ARGUS + Mistral |
|---|:---:|:---:|:---:|
| **Taux de réussite** | 19/20 (95%) | 20/20 (100%) | 20/20 (100%) |
| **Champs/doc (moyenne)** | 17.0 / 31 | 14.0 / 15 | 14.0 / 15 |
| **Confidence moyenne** | 0.819 | — | — |
| **OCR chars (moy.)** | 1,506 (markdown) | 869 | 1,464 |
| **Temps/doc (moy.)** | — | 24.9s | 23.8s |

### Observations clés

1. **Content Understanding** extrait le plus de champs (17/31) grâce à son schéma invoice prédéfini plus large (adresses détaillées, sous-champs, etc.)
2. **ARGUS + DocIntel** et **ARGUS + Mistral** atteignent tous deux 100% de réussite (20/20) avec un schéma personnalisé de 15 champs
3. **Mistral Doc AI** produit ~70% plus de texte OCR que Document Intelligence (1,464 vs 869 chars en moyenne), grâce à un formatage markdown plus riche
4. **Mistral** est légèrement plus rapide (23.8s vs 24.9s par document en moyenne)
5. Le document `batch1-0006` a échoué uniquement avec Content Understanding (0 champs extraits), tandis que les deux pipelines ARGUS l'ont traité avec succès

### Comparaison document par document

| Document | CU Champs | CU Conf. | DI Champs | DI OCR | DI Temps | MI Champs | MI OCR | MI Temps |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| batch1-0001 | 17/31 | 0.82 | 14/15 | 1,203 | 30.1s | 14/15 | 1,994 | 26.3s |
| batch1-0002 | 17/31 | 0.83 | 14/15 | 976 | 27.8s | 14/15 | 1,661 | 24.2s |
| batch1-0003 | 17/31 | 0.83 | 14/15 | 812 | 18.4s | 14/15 | 1,313 | 21.3s |
| batch1-0004 | 17/31 | 0.82 | 14/15 | 1,004 | 24.9s | 14/15 | 1,651 | 24.2s |
| batch1-0005 | 17/31 | 0.81 | 14/15 | 943 | 26.6s | 14/15 | 1,588 | 26.0s |
| batch1-0006 | **0/31** | 0.72 | 14/15 | 810 | 28.8s | 14/15 | 1,459 | 24.1s |
| batch1-0007 | 17/31 | 0.81 | 14/15 | 1,204 | 28.7s | 14/15 | 1,995 | 27.6s |
| batch1-0008 | 17/31 | 0.82 | 14/15 | 911 | 24.4s | 14/15 | 1,486 | 22.1s |
| batch1-0009 | 17/31 | 0.82 | 14/15 | 586 | 19.3s | 14/15 | 1,012 | 23.9s |
| batch1-0010 | 17/31 | 0.82 | 14/15 | 649 | 19.5s | 14/15 | 1,050 | 20.2s |
| batch1-0011 | 17/31 | 0.81 | 14/15 | 632 | 22.6s | 14/15 | 1,033 | 19.3s |
| batch1-0012 | 17/31 | 0.81 | 14/15 | 780 | 28.0s | 14/15 | 1,339 | 23.1s |
| batch1-0013 | 17/31 | 0.81 | 14/15 | 839 | 26.1s | 14/15 | 1,483 | 24.4s |
| batch1-0014 | 17/31 | 0.81 | 14/15 | 526 | 16.6s | 14/15 | 885 | 18.1s |
| batch1-0015 | 17/31 | 0.83 | 14/15 | 1,004 | 27.3s | 14/15 | 1,695 | 31.0s |
| batch1-0016 | 17/31 | 0.81 | 14/15 | 945 | 24.9s | 14/15 | 1,595 | 23.8s |
| batch1-0017 | 17/31 | 0.82 | 14/15 | 920 | 23.0s | 14/15 | 1,540 | 24.6s |
| batch1-0018 | 17/31 | 0.82 | 14/15 | 953 | 35.8s | 14/15 | 1,650 | 25.0s |
| batch1-0019 | 17/31 | 0.81 | 14/15 | 709 | 21.2s | 14/15 | 1,210 | 21.5s |
| batch1-0020 | 17/31 | 0.82 | 14/15 | 983 | 24.9s | 14/15 | 1,634 | 24.5s |

## 🏗️ Pipeline détaillé

### Méthode 1 — Content Understanding

```
Image JPG
  → Upload Azure Blob Storage (SAS URL)
  → Content Understanding API (prebuilt-invoice, v2025-11-01)
      → markdown structuré + 31 champs typés (automatique, 1 appel)
  → GPT-4.1 Vision (optionnel)
      → description textuelle du document
  → Sauvegarde JSON local
```

### Méthode 2 & 3 — ARGUS-style (DocIntel / Mistral)

```
Image JPG
  → Étape 1: OCR
      Option A: Azure Document Intelligence prebuilt-layout → markdown
      Option B: Mistral Document AI (mistral-document-ai-2505) → markdown
  → Étape 2: GPT-5-chat
      OCR text + image base64 + system prompt + schema JSON
      → extraction structurée (15 champs)
  → Sauvegarde JSON local (cache)
```

## 🔧 Services Azure utilisés

| Service | Ressource | Auth |
|---|---|---|
| Content Understanding | `aya-demo-ai.cognitiveservices.azure.com` | API Key |
| Document Intelligence | `docintel-argus-test.cognitiveservices.azure.com` | API Key (`Ocp-Apim-Subscription-Key`) |
| Mistral Document AI | `content-understanding--resource.services.ai.azure.com` | Bearer Token (Entra ID) |
| GPT-5-chat | `content-understanding--resource.cognitiveservices.azure.com` | Bearer Token (Entra ID) |

> **Note** : La ressource `content-understanding--resource` a l'authentification par clé désactivée. Mistral et GPT-5-chat nécessitent un Bearer token via `DefaultAzureCredential`.

## 📝 Schéma d'extraction ARGUS

Le schéma personnalisé utilisé pour les pipelines ARGUS contient **15 champs** :

```json
{
  "invoice_number": "string",
  "invoice_date": "string",
  "due_date": "string",
  "seller_name": "string",
  "seller_address": "string",
  "seller_tax_id": "string",
  "buyer_name": "string",
  "buyer_address": "string",
  "buyer_tax_id": "string",
  "iban": "string",
  "line_items": [{"description", "quantity", "unit_price", "net_worth", "vat_rate", "gross_worth"}],
  "subtotal": "number",
  "total_tax": "number",
  "total_amount": "number",
  "currency": "string"
}
```

## 🧪 Reproduction

1. Installer les dépendances :
   ```bash
   pip install python-dotenv requests azure-identity
   ```

2. Créer un fichier `.env` avec les credentials (voir `.env.example`)

3. Exécuter le notebook `comparison_cu_vs_argus.ipynb` cellule par cellule

## 📂 Format des résultats

Chaque fichier JSON de résultat ARGUS contient :

```json
{
  "file": "batch1-0001.jpg",
  "ocr_method": "DocIntel | Mistral",
  "error": null,
  "ocr_chars": 1203,
  "ocr_text_preview": "Invoice no: 51109338...",
  "extraction": {
    "invoice_number": "51109338",
    "invoice_date": "04/13/2013",
    "seller_name": "Andrews, Kirby and Valdez",
    "line_items": [...],
    "total_amount": 6204.19,
    ...
  },
  "fields_with_value": 14,
  "total_fields": 15,
  "time_seconds": 26.34
}
```

## 🔗 Références

- [Azure Content Understanding](https://learn.microsoft.com/azure/ai-services/content-understanding/)
- [ARGUS — Azure-Samples](https://github.com/Azure-Samples/ARGUS)
- [Azure Document Intelligence](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Mistral Document AI](https://docs.mistral.ai/capabilities/document/)
