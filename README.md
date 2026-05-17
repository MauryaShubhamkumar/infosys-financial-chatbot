# 📈 Infosys & IFRS Multi-Document Financial Analyst Chatbot

An advanced, agentic financial analyst chatbot built with **Streamlit**, **LangChain/LangGraph**, and **Google Gemini** that processes and reasons across multiple structured and unstructured financial data sources. It is specifically designed to handle **Infosys Annual Reports (PDFs)**, **IFRS Press Releases (PDFs)**, **Investor Sheets (Excel)**, and **Stock Price History (CSV)**.

---

## 🚀 Key Features

* **Multi-Format Data Loader**: Seamlessly ingests PDFs, Excel spreadsheets, and raw CSV files.
* **Agentic Routing (LangGraph)**: An autonomous AI agent architecture that routes financial queries dynamically to semantic vector stores, automated reporting tools, or custom data extraction paths.
* **Local Embeddings & FAISS Vector Store**: Uses Sentence-Transformers to construct high-quality, local vector embeddings, storing them in a local FAISS index for high-performance retrieval.
* **Interactive Conversational UI**: Built with Streamlit, supporting persistent chat history, document parsing status, and contextual dialogue.
* **On-the-fly Report Generation**: Automatically compiles complex financial queries into downloadable **PDF reports** or **Excel sheets** saved directly to the outputs folder.

---

## 📂 Project Structure

```text
financial-chatbot/
│
├── app.py                      # Streamlit application UI & configuration
├── requirements.txt            # Project python dependencies
├── .env.example                # Sample environment configuration file
├── .gitignore                  # Git ignore rules for virtual environments, API keys, etc.
│
├── data/                       # [Git Ignored] Place raw financial reports & sheets here
│   ├── infosys-ar-25.pdf
│   ├── ifrs-usd-press-release_q1.pdf
│   ├── investor-sheet.xls
│   └── 500209.csv
│
├── modules/                    # Core backend system modules
│   ├── loader.py               # Document loading utilities (PDF, XLS, CSV)
│   ├── vectorstore.py          # Embedding generation & local FAISS indexing
│   ├── chatbot.py              # LangGraph Agent setup & tool configurations
│   ├── report_generator.py     # Automated PDF/Excel report generators
│   └── utils.py                # Helper utilities
│
└── outputs/                    # [Git Ignored] Directory where generated PDF/XLS reports are saved
```

---

## 🛠️ Setup & Installation

Follow these steps to set up the project on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/MauryaShubhamkumar/infosys-financial-chatbot.git
cd infosys-financial-chatbot
```

### 2. Set Up a Python Virtual Environment
Initialize and activate your environment:

* **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If you hit script execution policy issues, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*

* **On macOS/Linux/Git Bash:**
  ```bash
  python3 -m venv venv
  source venv/Scripts/activate
  ```

### 3. Install Dependencies
Ensure you have the virtual environment active, then run:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root folder of the project:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## 📥 Ingesting Data

Since the input documents are heavy and contain proprietary financial information, the `data/` directory is **git-ignored**. You must place your source files inside the `data/` folder before launching:

1. Create a `data/` directory in the root folder if it doesn't already exist.
2. Put the following documents inside `data/`:
   * Infosys Annual Report (e.g., `infosys-ar-25.pdf`)
   * IFRS Quarterly Press Releases (`ifrs-usd-press-release_q1.pdf` to `q4.pdf`)
   * Investor Sheet (`investor-sheet.xls`)
   * Stock history CSV (`500209.csv`)

---

## 🏃 Running the Application

To launch the interactive dashboard:

```bash
streamlit run app.py
```

### In-App Execution Steps:
1. In the sidebar, click the **Process Documents** button to parse all PDFs, Excel, and CSV files, build the local embeddings, and create the FAISS index.
2. Once the processing is complete, you can start chatting with your AI Senior Financial Analyst in the main window!
3. Request detailed PDF summaries or data extractions, and the agent will generate them and provide direct download links right inside the chat window.
