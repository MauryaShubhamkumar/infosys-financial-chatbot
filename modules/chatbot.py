from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from modules.report_generator import generate_pdf, generate_excel
import json

def load_chatbot():

    # Must match the local model used in vectorstore.py
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    # Tool 1: Document Search
    @tool
    def search_financial_documents(query: str) -> str:
        """Searches the Infosys and IFRS financial documents. Always use this to answer questions about the documents. IMPORTANT: When you use this tool, the results will include metadata with 'source' (the document name). You MUST cite these sources in your final answer."""
        docs = retriever.invoke(query)
        result = ""
        for d in docs:
            result += f"\n[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}\n---\n"
        return result

    # Tool 2: PDF Generator
    @tool
    def create_pdf_report(content: str, filename: str) -> str:
        """Generates a downloadable PDF report. Use this when the user asks for a report, summary, or document.
        Provide the full, detailed markdown content and a suitable filename (e.g., 'Q3_Summary.pdf').
        Returns the path to the generated PDF. Always tell the user the file path so they can download it."""
        return generate_pdf(content, filename)

    # Tool 3: Excel Generator
    @tool
    def create_excel_report(data_json: str, filename: str) -> str:
        """Generates a downloadable Excel (.xlsx) file. Use this when the user asks for data in Excel, spreadsheet, or table format.
        data_json MUST be a valid JSON string representing a list of dictionaries, e.g. '[{"Metric": "Revenue", "Value": "100M"}]'.
        Returns the path to the generated Excel file. Always tell the user the file path so they can download it."""
        try:
            data = json.loads(data_json)
            return generate_excel(data, filename)
        except Exception as e:
            return f"Error parsing JSON data for Excel: {str(e)}"

    tools = [search_financial_documents, create_pdf_report, create_excel_report]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2
    )

    system_prompt = SystemMessage(content=(
        "You are an expert, genuinely intelligent financial analyst. You have access to Infosys financial reports. "
        "Always use the `search_financial_documents` tool to find accurate information before answering. "
        "When you answer, explicitly cite the document names you drew the information from (e.g., 'According to infosys-ar-25.pdf...'). "
        "If the user asks for a report or summary, use `create_pdf_report` and give them the exact file path in your response. "
        "If they ask for an Excel file or data spreadsheet, use `create_excel_report` and give them the exact file path. "
        "Present answers in a clean, structured way. If you don't know something or it's not in the documents, admit it directly."
    ))

    agent = create_react_agent(llm, tools, prompt=system_prompt)

    return agent