# 📄 Azure Content Understanding — Document Analysis (Batch 1)

## Description

Ce projet teste les **analyseurs pré-construits d'Azure AI Content Understanding** sur un lot de 20 documents scannés (factures, devis, bons de commande…).

Chaque document est analysé puis enrichi avec :
- **Extraction structurée des champs** (émetteur, montant, date, lignes d'articles…)
- **Description globale générée par GPT-4.1** déployé sur la ressource Cognitive Services

## Architecture

```
├── docu_prebuilt_invoice.ipynb    # Notebook principal d'analyse
├── .env                           # Clés API (non versionné)
├── .gitignore
├── batch_1/
│   ├── batch1_1/                  # 20 images sources (factures scannées JPG)
│   └── docu_results_batch1_1/     # Résultats JSON enrichis
│       └── prebuilt-invoice/      # 20 fichiers JSON enrichis
```

## Services Azure utilisés

| Service | Usage |
|---------|-------|
| **Azure AI Content Understanding** | Extraction de champs structurés (prebuilt-invoice) |
| **Azure Blob Storage** | Upload temporaire des images (SAS URL 2h) |
| **GPT-4.1 Vision** (Cognitive Services) | Description globale multimodale de chaque document |
| **Azure AD** | Authentification (DefaultAzureCredential) |

## Pipeline

1. **Authentification** — Token Azure AD (cache automatique)
2. **Upload Blob** — Chaque image est uploadée sur Azure Blob Storage
3. **Submit via URL** — L'URL SAS est envoyée à Content Understanding (⚠️ le format base64 inline ne fonctionne pas, voir section Tests)
4. **Batch Poll** — Récupération asynchrone des résultats
5. **Extraction des champs** — Parsing récursif des valeurs (valueString, valueNumber, valueDate…)
6. **Description LLM** — Envoi de l'image directement à GPT-4.1 Vision (indépendant de l'extraction)
7. **Sauvegarde** — JSON enrichi par document dans `docu_results_batch1_1/prebuilt-invoice/`

## Format de sortie (JSON enrichi)

Chaque fichier JSON de résultat contient :
- La réponse complète de Content Understanding (champs, markdown, tables, pages)
- Un bloc `_extracted` ajouté avec :
  - `field_values` : dictionnaire `{nom_champ: valeur}` (récursif pour sous-objets/tableaux)
  - `description` : description globale du document en français (2-3 phrases)

Exemple de `field_values` extrait (batch1-0001.json) :
```json
{
  "InvoiceId": "51109338",
  "InvoiceDate": "2013-04-13",
  "VendorName": "Andrews, Kirby and Valdez",
  "CustomerName": "Becker Ltd",
  "SubtotalAmount": {"Amount": 5640.17, "CurrencyCode": "USD"},
  "TotalTaxAmount": {"Amount": 564.02, "CurrencyCode": "USD"},
  "TotalAmount": {"Amount": 6204.19, "CurrencyCode": "USD"},
  "LineItems": [
    {"Description": "CLEARANCE! Fast Dell Desktop Computer PC...", "Quantity": 3, "UnitPrice": {"Amount": 209}, "TotalAmount": {"Amount": 689.7}},
    "... (7 articles au total)"
  ]
}
```

## 🧪 Tests et résultats

### Problème identifié : format base64 vs URL

Le format d'entrée `data` (base64 inline) documenté dans l'API **ne fonctionne pas** avec Content Understanding — l'API retourne `Succeeded` mais avec un markdown vide et 0 champ extrait.

| Test | Format d'entrée | Markdown | Champs extraits |
|------|-----------------|----------|-----------------|
| PDF Contoso (Microsoft sample) via **URL** | `{"url": "https://..."}` | ✅ 1641 chars | ✅ **22/31** |
| PDF Contoso via **base64** | `{"data": "<b64>", "mimeType": "application/pdf"}` | ❌ 13 chars (vide) | ❌ **0/31** |
| Notre JPEG via **base64** | `{"data": "<b64>", "mimeType": "image/jpeg"}` | ❌ 13 chars (vide) | ❌ **0/31** |
| Notre JPEG via **URL** (Blob SAS) | `{"url": "https://...blob...?sas"}` | ✅ 2011 chars | ✅ **13/31** |

**Conclusion** : il faut passer par une URL (Blob Storage + SAS token) pour que l'extraction fonctionne.

### Résultats du batch (20 documents)

```
batch1-0001.json: fields=17 | Facture émise par Andrews, Kirby and Valdez à Becker Ltd (6 204,19 $)
batch1-0002.json: fields=17 | [description: 429 rate limit]
batch1-0003.json: fields=17 | [description: 429 rate limit]
batch1-0004.json: fields=17 | [description: 429 rate limit]
batch1-0005.json: fields=17 | [description: 429 rate limit]
batch1-0006.json: fields=0  | [description: 429 rate limit] ← document atypique
batch1-0007.json: fields=17 | Facture émise par Wood, Simpson and...
batch1-0008.json: fields=17 | Facture émise par Hall-Boyd...
batch1-0009.json: fields=17 | [description: 429 rate limit]
batch1-0010.json: fields=17 | [description: 429 rate limit]
batch1-0011.json: fields=17 | [description: 429 rate limit]
batch1-0012.json: fields=17 | Facture n°13407985 émise le 22/11/2013 par Nicho...
batch1-0013.json: fields=17 | Facture émise par Schmidt LLC à Allen P...
batch1-0014.json: fields=17 | Facture émise par Tran, Hurst and Rodgers à Stephenson Inc...
batch1-0015.json: fields=17 | Facture (Invoice no: 46506594) émise le 03/12/2012...
batch1-0016.json: fields=17 | Facture émise par Austin and Sons...
batch1-0017.json: fields=17 | Facture n°98858130, émise le 28/01/2021...
batch1-0018.json: fields=17 | Facture émise par Lopez, Murray and Johnston...
batch1-0019.json: fields=17 | Facture (Invoice no: 56908352) émise le 01/11/2015...
batch1-0020.json: fields=17 | Facture (Invoice no: 15001300) émise le 18/02/2014...
```

**Bilan** :
- ✅ **19/20** documents : **17 champs** extraits avec valeurs réelles (InvoiceId, VendorName, CustomerName, TotalAmount, LineItems…)
- ⚠️ **1/20** document (batch1-0006) : 0 champs — document probablement atypique
- 📝 **12/20** descriptions LLM réussies, **8/20** erreurs 429 (rate limit GPT-4.1)
- 📈 Amélioration : **0/31 → 17/31 champs** grâce au passage base64 → URL

## Prérequis

- Python 3.10+
- Packages : `requests`, `azure-identity`, `azure-storage-blob`, `python-dotenv`
- Accès Azure AD avec les rôles :
  - **Cognitive Services User** sur la ressource AI
  - **Storage Blob Data Contributor** sur le compte de stockage
- Modèles déployés sur la ressource : `gpt-4.1`, `gpt-4.1-mini`, `text-embedding-3-large`

## Utilisation

```bash
pip install requests azure-identity azure-storage-blob python-dotenv
```

Ouvrir `docu_prebuilt_invoice.ipynb` et exécuter les cellules dans l'ordre.
