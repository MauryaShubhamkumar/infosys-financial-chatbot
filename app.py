import os
import streamlit as st
from dotenv import load_dotenv
from modules.loader import load_pdfs, load_excel, load_csv
from modules.vectorstore import create_vector_store
from modules.chatbot import load_chatbot
from langchain_core.messages import HumanMessage, AIMessage
import re

# Load environment variables from .env
load_dotenv()

st.set_page_config(page_title="Financial Analyst", page_icon="📈", layout="wide")
st.title("📈 Financial Analyst Chatbot")

# Initialize session state for UI messages and Langchain memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Senior Financial Analyst. I've read all the Infosys and IFRS documents. How can I help you today?"}
    ]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Document Processing")
    if st.button("Process Documents"):
        pdfs = [
            "data/infosys-ar-25.pdf",
            "data/ifrs-usd-press-release_q1.pdf",
            "data/ifrs-usd-press-release_q2.pdf",
            "data/ifrs-usd-press-release_q3.pdf",
            "data/ifrs-usd-press-release_q4.pdf"
        ]
        docs = []
        with st.spinner("Loading PDFs..."):
            docs.extend(load_pdfs(pdfs))
        with st.spinner("Loading Excel..."):
            docs.extend(load_excel("data/investor-sheet.xls"))
        with st.spinner("Loading CSV..."):
            docs.extend(load_csv("data/500209.csv"))
            
        create_vector_store(docs)
        st.success("Documents Processed Successfully!")
        st.rerun()

# Only show chat if FAISS index already exists
if os.path.exists("faiss_index"):
    # Load agent once per session
    if "agent" not in st.session_state:
        st.session_state.agent = load_chatbot()

    # Display chat messages from history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "file_path" in msg and msg["file_path"]:
                file_path = msg["file_path"]
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        btn_label = "📄 Download PDF Report" if file_path.endswith(".pdf") else "📊 Download Excel Data"
                        st.download_button(label=btn_label, data=f, file_name=os.path.basename(file_path), key=f"dl_{msg['content'][:10]}")

    # React to user input when input is given 
    if prompt := st.chat_input("Ask a financial question or request a report..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                messages = st.session_state.chat_history + [("user", prompt)]
                response = st.session_state.agent.invoke({"messages": messages})
                
                raw_content = response["messages"][-1].content
                # Gemini can return content as a list of parts instead of a string
                if isinstance(raw_content, list):
                    answer = "\n".join(
                        part.get("text", str(part)) if isinstance(part, dict) else str(part)
                        for part in raw_content
                    )
                else:
                    answer = str(raw_content)
                st.markdown(answer)
                
                # Check if the agent mentioned a file in outputs/
                file_path = None
                match = re.search(r'outputs[/\\][\w\.-]+', answer)
                if match:
                    file_path = match.group(0)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            btn_label = "📄 Download PDF Report" if file_path.endswith(".pdf") else "📊 Download Excel Data"
                            st.download_button(label=btn_label, data=f, file_name=os.path.basename(file_path), key="dl_new")
                
                # Save to memory
                msg_data = {"role": "assistant", "content": answer}
                if file_path:
                    msg_data["file_path"] = file_path
                st.session_state.messages.append(msg_data)
                
                st.session_state.chat_history.append(HumanMessage(content=prompt))
                st.session_state.chat_history.append(AIMessage(content=answer))

else:
    st.info(" Please click **Process Documents** in the sidebar to index your data files before chatting.")
