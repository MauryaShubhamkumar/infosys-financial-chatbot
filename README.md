# 📈 Infosys Financial Analyst Chatbot

This project is a financial analyst chatbot built using Streamlit, LangChain, FAISS, and Google Gemini API. It can answer financial questions from multiple Infosys financial documents including annual reports, quarterly IFRS press releases, investor sheets, and stock market data.

The chatbot supports conversational queries, document citations, follow-up questions, and automatic report generation in PDF or Excel format.

---

# Features

- Supports multiple document formats:
  - PDF
  - Excel
  - CSV

- Answers questions across all uploaded financial documents

- Uses FAISS vector database for semantic search

- Handles follow-up questions using conversation memory

- Shows source documents used to generate answers

- Generates:
  - PDF reports for summaries
  - Excel sheets for tabular financial data

- Simple Streamlit chat interface

---

# Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend |
| Streamlit | User Interface |
| LangChain | RAG Pipeline |
| Google Gemini API | LLM |
| FAISS | Vector Database |
| Pandas | Excel/CSV Processing |
| ReportLab | PDF Generation |

---

# Project Structure

```text
financial-chatbot/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── data/
│   ├── infosys-ar-25.pdf
│   ├── ifrs-usd-press-release_q1.pdf
│   ├── ifrs-usd-press-release_q2.pdf
│   ├── ifrs-usd-press-release_q3.pdf
│   ├── ifrs-usd-press-release_q4.pdf
│   ├── investor-sheet.xls
│   └── 500209.csv
│
├── modules/
│   ├── loader.py
│   ├── vectorstore.py
│   ├── chatbot.py
│   ├── report_generator.py
│   └── utils.py
│
└── outputs/
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/MauryaShubhamkumar/infosys-financial-chatbot.git

cd infosys-financial-chatbot
```

---

## 2. Create Virtual Environment

### Windows

```powershell
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Add Gemini API Key

Create a `.env` file in the root folder:

```env
GOOGLE_API_KEY=your_api_key_here
```

Get API key from:

https://aistudio.google.com/app/apikey

---

# Add Financial Documents

Create a `data/` folder and place all required financial files inside it:

- Annual Report PDF
- Quarterly IFRS PDFs
- Investor Excel Sheet
- Stock CSV File

---

# Run the Application

```bash
streamlit run app.py
```

---

# How It Works

1. Documents are loaded from PDFs, Excel, and CSV files
2. Text is split into smaller chunks
3. Embeddings are generated using Gemini Embeddings
4. FAISS stores document vectors locally
5. Relevant chunks are retrieved based on user queries
6. Gemini generates final responses using retrieved context

---

# Example Questions

- What was Infosys revenue growth in FY26?
- Compare Q1 and Q4 performance
- What were the major client wins in Q3?
- Summarize annual financial performance
- Compare operating margins across all quarters

---

# Author

Shubham KUmar Maurya  
B.Tech CSE, IIT Jammu