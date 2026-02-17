# 📄 Document Processing Benchmark — Streamlit App

Compare **Azure Content Understanding**, **Document Intelligence + GPT-5**, and **Mistral Doc AI (OCR)** on your own documents — all at once, side by side.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red)
![Azure](https://img.shields.io/badge/Azure-Content%20Understanding-0078D4)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 **Multi-doc upload** | Upload one or many documents (JPG, PNG, PDF, TIFF, BMP) |
| 🧾 **Prebuilt model picker** | Choose `prebuilt-invoice`, `prebuilt-layout`, or `prebuilt-read` |
| ⚡ **Parallel execution** | All 3 pipelines run simultaneously via thread pool |
| 📊 **Side-by-side comparison** | Metrics cards, comparison table, field-by-field diff |
| 📈 **Batch summary** | Aggregate stats & timing chart when processing multiple docs |
| 📥 **Export results** | Download full JSON results for further analysis |

## 🏗️ Architecture

```
Upload → ┌─── Azure Content Understanding (prebuilt analyzer)
         ├─── Azure Doc Intelligence + GPT-5-chat Vision
         └─── Mistral Doc AI (Azure-hosted OCR)
              ↓
         Side-by-side comparison & metrics
```

## 🚀 Quick Start

### 1. Install dependencies

```bash
cd benchmark_app
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual keys and endpoints
```

You need:
- **Azure Content Understanding** endpoint (with DefaultAzureCredential access)
- **Azure Blob Storage** account (for Content Understanding URL-based input)
- **Azure Document Intelligence** endpoint + key
- **Azure OpenAI** endpoint + key (with a GPT-5-chat deployment)
- **Mistral Doc AI** key (Azure-hosted Mistral OCR)

### 3. Run the app

```bash
streamlit run app.py
```

### 4. Use the app

1. Pick a **prebuilt model** in the sidebar
2. Select which **pipelines** to run
3. **Upload** your documents
4. Click **🚀 Run Benchmark**
5. Explore the results!

## 📁 Project Structure

```
benchmark_app/
├── app.py                          # Main Streamlit application
├── config.py                       # Configuration (env vars)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── README.md                       # This file
├── services/
│   ├── content_understanding.py    # Azure Content Understanding API
│   ├── doc_intel_gpt.py            # Doc Intelligence + GPT-5-chat Vision
│   └── mistral_vision.py           # Mistral Doc AI (Azure-hosted OCR)
└── utils/
    └── comparison.py               # Comparison tables & metrics
```

## 🔧 Configuration Details

| Variable | Description |
|----------|-------------|
| `AZURE_CU_ENDPOINT` | Content Understanding cognitive services endpoint |
| `AZURE_STORAGE_ACCOUNT` | Storage account for blob temp uploads |
| `AZURE_STORAGE_CONTAINER` | Blob container name (default: `cu-temp`) |
| `DOC_INTELLIGENCE_ENDPOINT` | Document Intelligence endpoint |
| `DOC_INTELLIGENCE_KEY` | Document Intelligence API key |
| `GPT_ENDPOINT` | Full GPT-5-chat completions URL (includes deployment + api-version) |
| `GPT_KEY` | GPT API key |
| `MISTRAL_DOC_AI_ENDPOINT` | Azure-hosted Mistral OCR endpoint |
| `MISTRAL_DOC_AI_KEY` | Mistral Doc AI API key |
| `MISTRAL_DOC_AI_MODEL` | Mistral model name (default: `mistral-document-ai-2505`) |
