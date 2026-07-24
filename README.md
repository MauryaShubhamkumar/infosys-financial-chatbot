# 📈 Financial Analyst Chatbot

This project is a deployment-ready AI Financial Analyst Chatbot built using Streamlit, LangChain, FAISS, and Google Gemini API. Users can upload their own financial documents (PDFs, Excel spreadsheets, and CSV files) via a dedicated sidebar workflow.

The chatbot supports conversational queries, document citations, follow-up questions, incremental indexing, FAISS persistence, and automatic report generation in PDF or Excel format.

---

# Key Features

- **Sidebar File Upload Workflow**: Users upload custom PDF, Excel (`.xlsx`, `.xls`), and CSV files directly from the sidebar.
- **Session-Based Storage**: Uploaded files are organized into unique timestamped session folders (`uploads/session_YYYYMMDD_HHMMSS/`).
- **Upload Metrics & Validation**: Real-time display of total uploaded files and total file size in MB/KB with 0-byte file filtering.
- **Incremental Document Indexing**: Tracks SHA-256 hashes and modification timestamps to re-embed only new or modified documents.
- **Smart Startup & FAISS Persistence**: Loads existing vector indexes in seconds on app launch without re-embedding unchanged documents.
- **Report Generation**: Automatically creates downloadable PDF reports or structured Excel files.

---

# Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend Engine |
| Streamlit | Interactive Web UI |
| LangChain | RAG & Agent Pipeline |
| Google Gemini API | LLM (`gemini-2.5-flash`) |
| HuggingFace / FAISS | Embedding Model (`all-MiniLM-L6-v2`) & Vector Database |
| Pandas | Excel / CSV Processing |
| ReportLab | PDF Generation |

---

# Project Structure

```text
financial-chatbot/
│
├── app.py                      # Main Streamlit Application UI
├── requirements.txt            # Package Dependencies
├── .env.example                # Environment Variable Template
├── .gitignore                  # Git Ignore Rules
│
├── modules/
│   ├── loader.py               # PDF, Excel, and CSV Document Loaders (@st.cache_data)
│   ├── vectorstore.py          # Vector Store, Incremental Indexing & FAISS Management
│   ├── chatbot.py             # LangChain / LangGraph Chatbot Agent Definition
│   ├── report_generator.py     # PDF & Excel Report Generators
│   └── utils.py                # SHA-256 Hashing, Metadata, & Session Storage Utils
│
├── uploads/                    # User Session Upload Directories
│   └── session_YYYYMMDD_HHMMSS/
│
├── faiss_index/                # FAISS Index, Hash Database & Index Metadata
│   ├── index.faiss
│   ├── index.pkl
│   ├── file_hashes.json
│   └── doc_metadata.json
│
└── outputs/                    # Generated PDF and Excel Reports
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

Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

# Run the Application

```bash
streamlit run app.py
```

---

# User Workflow

1. Open the application in your browser.
2. In the sidebar under **📂 Upload Documents**, select one or more PDF, Excel, or CSV files.
3. Review uploaded files, file count, and total upload size.
4. Click **Process Documents**.
5. The application builds/updates the FAISS index with progress feedback.
6. Start asking questions and requesting PDF or Excel reports in the chat!

---

# Author

Shubham Kumar Maurya  
B.Tech CSE, IIT Jammu