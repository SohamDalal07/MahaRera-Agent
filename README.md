# MahaRERA Compliance Auditor
An automated, AI-powered compliance auditing platform that cross-references **Builder-Buyer Agreements** against official **MahaRERA (Maharashtra Real Estate Regulatory Authority)** regulations, general rules, and circulars.
---
## 🚀 Key Features
*   **Hybrid OCR Extraction:** Automatically scans PDF pages for legacy Marathi font corruption (e.g. *Shivaji* or *KrutiDev* fonts) and uses **EasyOCR (PyTorch)** to extract clean, searchable Unicode text.
*   **Semantic Search & RAG:** Chunks official regulations, vectorizes them using `BAAI/bge-base-en-v1.5`, and searches the **FAISS vector database** to retrieve the exact legal provisions matching any agreement clause.
*   **Automated Audits:** Evaluates clauses in batches of 5 using the **Google Gemini API** to ensure maximum reliability and lower token consumption.
*   **Sleek Results Dashboard:** A premium, modern React dashboard that separates findings into:
    *   *Original Text*
    *   *Compliance Reasoning*
    *   *Source Regulatory citations*
    *   *Actionable Recommendations*
*   **SHA-256 Audit Cache:** Computes file hashes to instantly render compliance reports (<100ms) for previously uploaded agreements, bypassing Gemini quota hits.
*   **Self-Healing Fallback:** Seamlessly redirects LLM queries to a local **Ollama (Qwen 2.5:7b)** model if Gemini hits rate limits or quota exhaustion.
---
## 🛠️ Tech Stack
*   **Frontend:** React.js, Vite, Vanilla CSS (Modern gradients, micro-animations, glassmorphism).
*   **Backend:** FastAPI, Uvicorn, Python 3.10+.
*   **Vector Search Database:** FAISS (Facebook AI Similarity Search).
*   **Embedding Model:** Hugging Face `BAAI/bge-base-en-v1.5`.
*   **OCR Engine:** EasyOCR (PyTorch).
*   **Primary LLM:** Google Gemini API (`gemini-1.5-flash` or `gemini-3.5-flash`).
*   **Local LLM Fallback:** Ollama (`qwen2.5:7b`).
---
## 📂 Project Structure
```text
MahaRera/
├── project/                # Backend internal library (OCR loaders, LLM config, prompts)
├── vector_store/           # FAISS Vector Index database files
├── uploads/                # Local cache files (OCR page texts and audit reports)
├── knowledge_base/         # Official MahaRERA rules, acts, circulars, and FAQs
├── main.py                 # FastAPI backend server
├── ingest.py               # Ingestion script to build the vector store
├── requirements.txt        # Python dependencies
└── frontend/               # Vite + React frontend web application
```
---
