---
title: ERIA - Education Regulation Impact Analyzer
emoji: ⚖️
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: true
license: mit
---

# ⚖️ ERIA — Education Regulation Impact Analyzer (v2.2.0)

> **GUVI Capstone Project** | Domain: EdTech / Education Policy Analytics

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://huggingface.co/spaces/pravinkumardatafreak/ERIA-Education-Analyzer)
**Live Demo Link:** [https://huggingface.co/spaces/pravinkumardatafreak/ERIA-Education-Analyzer](https://huggingface.co/spaces/pravinkumardatafreak/ERIA-Education-Analyzer)

ERIA is an AI-powered platform that converts complex, unstructured education regulation documents (UGC, AICTE, NAAC, NIRF, Ministry of Education) into structured, action-oriented, and stakeholder-specific insights.

---

## 📌 GitHub Repository Details
*If you are deploying or setting up this repository on GitHub, you can use these details for your repository settings:*

* **Description:** An AI-powered Education Regulation Impact Analyzer built using Streamlit, Groq API (LLaMA 3.3 70B), and a local Hugging Face transformer pipeline for dynamic emotion/sentiment mapping on stakeholders, featuring a self-correction multi-agent loop and an in-memory RAG pipeline.
* **Topics:** `nlp`, `transformers`, `multi-agent-system`, `streamlit`, `groq-api`, `llama3`, `rag`, `policy-analytics`, `edtech`, `data-science-capstone`
>>>>>>> 21c3086 (refactor: expand emotion classification to all stakeholders and clean redundant test files)

---
## 🚀 Features

| Feature | Technical Implementation | Description |
|---|---|---|
| 📄 Document Ingestion | `pdfplumber` & `BeautifulSoup4` | Extract text cleanly from local PDFs or scrape web URLs / online PDFs. |
| 🔍 Lightweight RAG | `scikit-learn` TF-IDF + Cosine Similarity | Splits documents into overlapping word chunks and retrieves the top relevant context to optimize token count. |
| 🤖 Agentic Analysis | Groq API (`llama-3.3-70b-versatile`) | Multi-agent self-correction loop featuring an Analyst, Critic, Refiner, and Strategist. |
| 📝 Self-Correction | Critic (LLM-as-a-Judge) | The Critic rates draft analysis out of 10 for Grounding, Consistency, and Completeness, prompting refinement on issues. |
| 🎭 Emotion Tagging | Local Hugging Face Pipeline (`DistilRoBERTa`) | Classifies stakeholder impact text into 7 emotion states (*joy, sadness, anger, fear, surprise, disgust, neutral*) in real-time. |
| 📊 Visual Analytics | `Plotly` (Graph Objects) | Renders interactive sentiment bar charts and risk gauges on the Streamlit dashboard. |
| 📈 Forecasts | LLaMA 3.3 70B Reasoner | Maps short-term (0–1 yr), medium-term (1–5 yrs), and long-term (>5 yrs) downstream impacts. |
| 🧭 Strategic Framework | OECD Regulatory Impact Standards | Assesses Compliance Burden, Fiscal Metrics, Equity Metrics, and Academic Quality with concrete EdTech opportunities. |
| 🕰️ Policy Chronology | Parametric & RAG retrieval | Tracks historical policy timelines and context relating back to foundational circulars (e.g., NEP 2020). |
| 📥 PDF Report | `fpdf2` PDF Generator | Downloads a beautifully structured and color-coded executive analysis report. |

---

## 🛠️ Tech Stack

* **Front-end UI**: Streamlit (v1.35.0+)
* **LLM Engine**: Groq API (LLaMA 3.3 70B Versatile)
* **Local NLP Modeling**: Hugging Face Transformers (`pipeline`), PyTorch (`torch`), Scikit-learn (`TfidfVectorizer`, `cosine_similarity`)
* **Data Visualization**: Plotly (v5.18.0+)
* **Text Extraction & Scraping**: pdfplumber (v0.11.0+), BeautifulSoup4 (v4.12.0+)
* **Report Generation**: fpdf2 (v2.7.9+)
* **Environment Management**: python-dotenv (v1.0.0+)

---

## 📂 Project Structure

```
ERIA/
├── .streamlit/
│   └── config.toml             # Custom theme colors (dark mode) & configurations
├── assets/
│   └── logo.png                # System logo image asset
├── modules/
│   ├── __init__.py
│   ├── document_processor.py   # PDF text extraction, web scraping, and RAG chunks retrieval
│   ├── llm_analyzer.py         # Multi-agent loop (Analyst/Critic/Refiner/Strategist) & Groq calls
│   ├── emotion_analyzer.py     # Local DistilRoBERTa Hugging Face emotion classifier
│   └── report_generator.py     # Styled PDF report generator with UTF-8 character sanitization
├── app.py                      # Main Streamlit dashboard interface & UI flow
├── packages.txt                # Headless Linux system dependencies for Hugging Face Spaces
├── requirements.txt            # Python dependencies (Streamlit, Groq, Torch, Transformers, etc.)
├── .env.example                # Template for environment API keys
├── .gitignore                  # Exclusion list (ignores local .env and generated *.pdf files)
├── VIVA_AND_STUDY_GUIDE.md     # Detailed self-study and Capstone evaluation prep guide
└── README.md                   # Project landing page and deployment metadata
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/pravinkumardatafreak/ERIA-Education-Analyzer.git
cd ERIA
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```
*(Note: Initial run will download the local DistilRoBERTa weights (~300MB) automatically via Hugging Face).*

### 4. Configure your API key
Create a `.env` file in the root folder (or copy from `.env.example`):
```bash
copy .env.example .env
```
Open `.env` and fill in your Groq API Key:
```env
GROQ_API_KEY=your_groq_api_key_here
```
Get your free API key at [console.groq.com](https://console.groq.com).

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🔑 Key Evaluation Metrics
*These metrics measure system performance for project verification:*

| Metric | Target / Benchmark | Description |
|---|---|---|
| **Topic Categorization** | >95% Accuracy | Categorizing regulations into Accreditation, Scholarship, Curriculum, etc. |
| **Grounding Score** | $\ge$ 8/10 | Rated by the Critic agent to prevent LLM hallucinations. |
| **Response Latency** | <15 seconds | Total RAG text extraction, Multi-Agent Loop, and local Emotion Inference time. |
| **PDF Format Safety** | 0 character crashes | Complete replacement of non-Latin-1 characters to protect document compile. |

---

## 📝 License & Attribution
This project is developed as part of the **GUVI Zen Class Data Science Capstone Project**.

*Built with ❤️ using Groq LLaMA 3.3 70B, Hugging Face Transformers, and Streamlit.*
