# ⚖️ ERIA — Education Regulation Impact Analyzer

> **GUVI Capstone Project** | Domain: EdTech / Education Policy Analytics

ERIA is an AI-powered platform that converts complex education regulation documents
(UGC, AICTE, NAAC, NIRF, Ministry of Education) into simple, stakeholder-friendly insights.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📄 PDF Upload | Extract and analyze any regulation PDF |
| 🌐 URL Scraping | Directly scrape and analyze URLs |
| 🤖 LLM Analysis | Powered by **Groq (LLaMA 3.3 70B)** for ultra-fast inference |
| 👥 Stakeholder Impact | Mapped for Students, Faculty, Institutions, Admins |
| 📈 Visual Analytics | Interactive **Plotly** Sentiment Maps and Risk Gauges |
| 📈 Impact Forecast | Short / Medium / Long term assessment |
| ⚠️ Risk Detection | Identifies risks, compliance gaps, and opportunities |
| 🕰️ Chronology | Policy history and amendment tracking |
| 📥 PDF Report | Downloadable branded analysis report |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** – Dashboard UI
- **Groq API** – LLaMA 3.3 70B LLM engine
- **Plotly** – Interactive data visualizations
- **pdfplumber** – PDF text extraction
- **BeautifulSoup4** – Web scraping
- **fpdf2** – PDF report generation
- **python-dotenv** – Environment variable management

---

## 📂 Project Structure

```
ERIA/
├── app.py                      # Main Streamlit dashboard
├── modules/
│   ├── __init__.py
│   ├── document_processor.py   # PDF & URL text extraction
│   ├── llm_analyzer.py         # Groq API integration & prompting
│   └── report_generator.py     # PDF report generation
├── requirements.txt            # Project dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ERIA.git
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

### 4. Configure your API key
```bash
copy .env.example .env
# Edit .env and add your GROQ_API_KEY
```
Get your free API key at: [https://console.groq.com](https://console.groq.com)

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🔑 Getting a Free Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign in with your account
3. Click **"API Keys"** → **"Create API Key"**
4. Copy and paste into the sidebar of the app

---

## 📊 Evaluation Metrics

| Metric | Description |
|---|---|
| Topic Classification Accuracy | Correctly identifies regulation category |
| Stakeholder Relevance | Impact details are accurate and specific |
| Summarization Quality | Summary is clear and easy to understand |
| Processing Time | Document analyzed in under 15 seconds (Groq Speed) |
| Report Quality | PDF report is readable and complete |

---

## 📚 Official Regulation Sources

- [UGC Circulars](https://www.ugc.gov.in/Circulars)
- [UGC Regulations](https://www.ugc.gov.in/regulations)
- [UGC Notices](https://www.ugc.gov.in/Notices)
- [UGC Guidelines](https://www.ugc.gov.in/Guideline)
- [AICTE](https://www.aicte-india.org)
- [NAAC](https://naac.gov.in)

---

## 📝 License

This project is developed as part of the **GUVI Zen Class Data Science Capstone Project**.

---

*Built with ❤️ using Groq LLaMA 3.3 70B and Streamlit*
