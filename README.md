# u{1F4C4} Azure Content Understanding u{2014} Document Analysis (Batch 1)

## Description

Ce projet teste les **analyseurs pru{00E9}-construits d'Azure AI Content Understanding** sur un lot de 20 documents scannu{00E9}s (factures), puis **compare 3 mu{00E9}thodes** d'extraction documentaire :

1. **Content Understanding** u{2014} API pru{00E9}-entrau{00EE}nu{00E9}e `prebuilt-invoice`
2. **ARGUS + Document Intelligence** u{2014} Pipeline OCR + GPT-5-chat
3. **ARGUS + Mistral Document AI** u{2014} Pipeline OCR + GPT-5-chat

> Pipeline ARGUS inspiru{00E9} de [Azure-Samples/ARGUS](https://github.com/Azure-Samples/ARGUS)

## u{1F3D7}u{FE0F} Architecture du projet

```
u{251C}u{2500}u{2500} docu_prebuilt_invoice.ipynb          # Notebook Content Understanding (Mu{00E9}thode 1)
u{251C}u{2500}u{2500} .env                                 # Clu{00E9}s API (non versionnu{00E9})
u{251C}u{2500}u{2500} .gitignore
u{251C}u{2500}u{2500} batch_1/
u{2502}   u{251C}u{2500}u{2500} batch1_1/                        # 20 images sources (factures scannu{00E9}es JPG)
u{2502}   u{2514}u{2500}u{2500} docu_results_batch1_1/           # Ru{00E9}sultats
u{2502}       u{251C}u{2500}u{2500} comparison_cu_vs_argus.ipynb  # Notebook de comparaison (3 mu{00E9}thodes)
u{2502}       u{251C}u{2500}u{2500} all_metrics.json              # Mu{00E9}triques globales
u{2502}       u{251C}u{2500}u{2500} model_comparison_summary.json # Ru{00E9}sumu{00E9} comparatif
u{2502}       u{251C}u{2500}u{2500} prebuilt-invoice/             # Ru{00E9}sultats Content Understanding (20 docs)
u{2502}       u{251C}u{2500}u{2500} prebuilt-layout/              # Ru{00E9}sultats Doc Intelligence layout (18 docs)
u{2502}       u{251C}u{2500}u{2500} prebuilt-read/                # Ru{00E9}sultats Doc Intelligence read (18 docs)
u{2502}       u{251C}u{2500}u{2500} argus-style-di/               # Ru{00E9}sultats ARGUS + DocIntel OCR (20 docs)
u{2502}       u{2514}u{2500}u{2500} argus-style-mistral/          # Ru{00E9}sultats ARGUS + Mistral OCR (20 docs)
```

## u{1F52C} Mu{00E9}thodes comparu{00E9}es

| | Mu{00E9}thode 1 u{2014} Content Understanding | Mu{00E9}thode 2 u{2014} ARGUS + DocIntel | Mu{00E9}thode 3 u{2014} ARGUS + Mistral |
|---|---|---|---|
| **OCR** | `prebuilt-invoice` (API intu{00E9}gru{00E9}e) | `prebuilt-layout` (Document Intelligence) | `mistral-document-ai-2505` (Mistral Doc AI) |
| **Extraction** | Modu{00E8}le pru{00E9}-entrau{00EE}nu{00E9} (31 champs fixes) | GPT-5-chat (schu{00E9}ma personnalisable, 15 champs) | GPT-5-chat (schu{00E9}ma personnalisable, 15 champs) |
| **Approche** | Extraction directe en 1 appel | Pipeline OCR u{2192} LLM (2 u{00E9}tapes) | Pipeline OCR u{2192} LLM (2 u{00E9}tapes) |
| **Philosophie** | Schu{00E9}ma fixe Microsoft | Flexible, inspiru{00E9} [ARGUS](https://github.com/Azure-Samples/ARGUS) | Flexible, inspiru{00E9} [ARGUS](https://github.com/Azure-Samples/ARGUS) |

---

## u{1F4CA} Ru{00E9}sultats u{2014} Comparaison (20 factures)

### Mu{00E9}triques agru{00E9}gu{00E9}es

| Mu{00E9}trique | Content Understanding | ARGUS + DocIntel | ARGUS + Mistral |
|---|:---:|:---:|:---:|
| **Taux de ru{00E9}ussite** | 19/20 (95%) | 20/20 (100%) | 20/20 (100%) |
| **Champs/doc (moyenne)** | 17.0 / 31 | 14.0 / 15 | 14.0 / 15 |
| **Confidence moyenne** | 0.819 | u{2014} | u{2014} |
| **OCR chars (moy.)** | 1,506 (markdown) | 869 | 1,464 |
| **Temps/doc (moy.)** | u{2014} | 24.9s | 23.8s |

### Observations clu{00E9}s

1. **Content Understanding** extrait le plus de champs (17/31) gru{00E2}ce u{00E0} son schu{00E9}ma invoice pru{00E9}du{00E9}fini plus large
2. **ARGUS + DocIntel** et **ARGUS + Mistral** atteignent 100% de ru{00E9}ussite (20/20) avec un schu{00E9}ma personnalisu{00E9} de 15 champs
3. **Mistral Doc AI** produit ~70% plus de texte OCR que Document Intelligence (1,464 vs 869 chars), gru{00E2}ce u{00E0} un formatage markdown plus riche
4. **Mistral** est lu{00E9}gu{00E8}rement plus rapide (23.8s vs 24.9s par document)
5. Le document `batch1-0006` a u{00E9}chouu{00E9} uniquement avec Content Understanding (0 champs), les deux pipelines ARGUS l'ont traitu{00E9} avec succu{00E8}s

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

---

## u{1F3D7}u{FE0F} Pipelines du{00E9}taillu{00E9}s

### Mu{00E9}thode 1 u{2014} Content Understanding

```
Image JPG
  u{2192} Upload Azure Blob Storage (SAS URL)
  u{2192} Content Understanding API (prebuilt-invoice, v2025-11-01)
      u{2192} markdown structuru{00E9} + 31 champs typu{00E9}s (automatique, 1 appel)
  u{2192} GPT-4.1 Vision (optionnel)
      u{2192} description textuelle du document
  u{2192} Sauvegarde JSON local
```

### Mu{00E9}thode 2 & 3 u{2014} ARGUS-style (DocIntel / Mistral)

```
Image JPG
  u{2192} u{00C9}tape 1: OCR
      Option A: Azure Document Intelligence prebuilt-layout u{2192} markdown
      Option B: Mistral Document AI (mistral-document-ai-2505) u{2192} markdown
  u{2192} u{00C9}tape 2: GPT-5-chat
      OCR text + image base64 + system prompt + schema JSON
      u{2192} extraction structuru{00E9}e (15 champs)
  u{2192} Sauvegarde JSON local (cache)
```

---

## u{1F527} Services Azure utilisu{00E9}s

| Service | Ressource | Auth |
|---|---|---|
| Content Understanding | `aya-demo-ai.cognitiveservices.azure.com` | API Key |
| Document Intelligence | `docintel-argus-test.cognitiveservices.azure.com` | API Key (`Ocp-Apim-Subscription-Key`) |
| Mistral Document AI | `content-understanding--resource.services.ai.azure.com` | Bearer Token (Entra ID) |
| GPT-5-chat | `content-understanding--resource.cognitiveservices.azure.com` | Bearer Token (Entra ID) |
| Azure Blob Storage | Upload temporaire (SAS URL 2h) | Azure AD |

> **Note** : La ressource `content-understanding--resource` a l'authentification par clu{00E9} du{00E9}sactivu{00E9}e. Mistral et GPT-5-chat nu{00E9}cessitent un Bearer token via `DefaultAzureCredential`.

---

## u{1F9EA} Tests Content Understanding u{2014} Format base64 vs URL

| Test | Format d'entru{00E9}e | Markdown | Champs extraits |
|------|-----------------|----------|-----------------|
| PDF Contoso via **URL** | `{"url": "https://..."}` | u{2705} 1641 chars | u{2705} **22/31** |
| PDF Contoso via **base64** | `{"data": "<b64>", "mimeType": "..."}` | u{274C} 13 chars | u{274C} **0/31** |
| JPEG via **base64** | `{"data": "<b64>", "mimeType": "image/jpeg"}` | u{274C} 13 chars | u{274C} **0/31** |
| JPEG via **URL** (Blob SAS) | `{"url": "https://...blob...?sas"}` | u{2705} 2011 chars | u{2705} **13/31** |

**Conclusion** : le format base64 inline ne fonctionne pas avec Content Understanding. Il faut passer par une URL (Blob Storage + SAS token).

---

## u{1F4DD} Schu{00E9}ma d'extraction ARGUS

Le schu{00E9}ma personnalisu{00E9} utilisu{00E9} pour les pipelines ARGUS contient **15 champs** :

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

---

## u{1F4C2} Format des ru{00E9}sultats

### Content Understanding (prebuilt-invoice)

Chaque JSON contient la ru{00E9}ponse complu{00E8}te + un bloc `_extracted` :
```json
{
  "InvoiceId": "51109338",
  "InvoiceDate": "2013-04-13",
  "VendorName": "Andrews, Kirby and Valdez",
  "TotalAmount": {"Amount": 6204.19, "CurrencyCode": "USD"},
  "LineItems": [{"Description": "...", "Quantity": 3, "UnitPrice": {"Amount": 209}}]
}
```

### ARGUS-style (DocIntel / Mistral)

```json
{
  "file": "batch1-0001.jpg",
  "ocr_method": "DocIntel | Mistral",
  "ocr_chars": 1203,
  "extraction": {
    "invoice_number": "51109338",
    "seller_name": "Andrews, Kirby and Valdez",
    "total_amount": 6204.19,
    "line_items": [...]
  },
  "fields_with_value": 14,
  "time_seconds": 26.34
}
```

---

## u{1F680} Utilisation

### Pru{00E9}requis

- Python 3.10+
- Packages : `requests`, `azure-identity`, `azure-storage-blob`, `python-dotenv`
- Accu{00E8}s Azure AD avec les ru{00F4}les :
  - **Cognitive Services User** sur la ressource AI
  - **Storage Blob Data Contributor** sur le compte de stockage

### Installation

```bash
pip install requests azure-identity azure-storage-blob python-dotenv
```

### Exu{00E9}cution

1. Cru{00E9}er un fichier `.env` avec les credentials
2. **Mu{00E9}thode 1** : Exu{00E9}cuter `docu_prebuilt_invoice.ipynb`
3. **Mu{00E9}thodes 2 & 3** : Exu{00E9}cuter `batch_1/docu_results_batch1_1/comparison_cu_vs_argus.ipynb`

---

## u{1F517} Ru{00E9}fu{00E9}rences

- [Azure Content Understanding](https://learn.microsoft.com/azure/ai-services/content-understanding/)
- [ARGUS u{2014} Azure-Samples](https://github.com/Azure-Samples/ARGUS)
- [Azure Document Intelligence](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Mistral Document AI](https://docs.mistral.ai/capabilities/document/)
