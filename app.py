import os
import sys
import asyncio
import importlib

# Fix Python 3.13 / Windows asyncio event loop closed RuntimeError during Streamlit runner cleanup
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

    _original_call_soon_threadsafe = asyncio.BaseEventLoop.call_soon_threadsafe

    def _safe_call_soon_threadsafe(self, callback, *args, **context):
        try:
            if not self.is_closed():
                return _original_call_soon_threadsafe(self, callback, *args, **context)
        except RuntimeError:
            pass

    asyncio.BaseEventLoop.call_soon_threadsafe = _safe_call_soon_threadsafe

import re
import time
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Import and reload modules to prevent Streamlit sys.modules stale cache issues
import modules.loader as loader_module
import modules.utils as utils_module
import modules.vectorstore as vectorstore_module
import modules.chatbot as chatbot_module

try:
    importlib.reload(loader_module)
    importlib.reload(utils_module)
    importlib.reload(vectorstore_module)
    importlib.reload(chatbot_module)
except Exception:
    pass

load_pdfs = loader_module.load_pdfs
load_excel = loader_module.load_excel
load_csv = loader_module.load_csv

create_vector_store = vectorstore_module.create_vector_store
load_faiss_index = vectorstore_module.load_faiss_index
process_incremental_indexing = getattr(
    vectorstore_module,
    "process_incremental_indexing",
    lambda *args, **kwargs: (None, {})
)

load_chatbot = chatbot_module.load_chatbot

format_file_size = utils_module.format_file_size
get_or_create_session_dir = utils_module.get_or_create_session_dir
save_session_uploaded_files = utils_module.save_session_uploaded_files
get_session_active_files = utils_module.get_session_active_files
get_document_hashes = utils_module.get_document_hashes
load_saved_hashes = utils_module.load_saved_hashes
save_file_hashes = utils_module.save_file_hashes
has_documents_changed = utils_module.has_documents_changed
validate_faiss_index = utils_module.validate_faiss_index
load_index_metadata = utils_module.load_index_metadata
save_index_metadata = utils_module.save_index_metadata
load_doc_metadata = utils_module.load_doc_metadata
analyze_document_changes = utils_module.analyze_document_changes
safe_clean_index = utils_module.safe_clean_index

# Load environment variables from .env
load_dotenv()

st.set_page_config(page_title="Financial Analyst", page_icon="📈", layout="wide")
st.title("📈 Financial Analyst Chatbot")

# Initialize session state for UI messages and LangChain memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your Senior Financial Analyst. I've read your uploaded documents. How can I help you today?"
        }
    ]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get or initialize unique session folder (e.g. uploads/session_20260724_234818)
session_dir = get_or_create_session_dir("uploads")

# ====================================================
# SIDEBAR CONTROL, FILE UPLOAD & STATUS PANEL
# ====================================================
with st.sidebar:
    st.header("📂 Upload Documents")

    # Feature: Streamlit file_uploader for multiple documents
    uploaded_files = st.file_uploader(
        "Upload Files",
        type=["pdf", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Upload PDF, Excel, or CSV financial documents"
    )

    # Save uploaded non-empty files into the active session folder
    if uploaded_files:
        save_session_uploaded_files(uploaded_files, session_dir)

    # Discover active files in the session folder
    pdf_files, excel_files, csv_files, total_bytes = get_session_active_files(session_dir)

    # Fallback to general uploads directory if active session is empty but uploads has files
    if not (pdf_files or excel_files or csv_files):
        # Scan any subdirectories or files in base uploads
        for item in os.listdir("uploads"):
            item_path = os.path.join("uploads", item)
            if os.path.isdir(item_path):
                p, e, c, b = get_session_active_files(item_path)
                if p or e or c:
                    pdf_files, excel_files, csv_files, total_bytes = p, e, c, b
                    break

    all_active_files = pdf_files + excel_files + csv_files
    total_file_count = len(all_active_files)
    formatted_total_size = format_file_size(total_bytes)

    st.markdown("""
**Supported:**  
✓ PDF (`.pdf`)  
✓ Excel (`.xlsx`, `.xls`)  
✓ CSV (`.csv`)  
""")

    if total_file_count > 0:
        st.markdown("**Uploaded Files:**")
        for fpath in all_active_files:
            fname = os.path.basename(fpath)
            icon = "📄" if fname.lower().endswith(".pdf") else ("📊" if fname.lower().endswith((".xls", ".xlsx")) else "📈")
            st.markdown(f"{icon} `{fname}`")

        st.markdown(f"**Files Uploaded:** `{total_file_count}`")
        st.markdown(f"**Total Size:** `{formatted_total_size}`")
    else:
        st.info("No files uploaded yet. Please upload documents to begin.")

    process_btn = st.button("Process Documents", disabled=(total_file_count == 0))

    st.markdown("---")
    st.subheader("System Status")


def render_scan_analysis(analysis: dict, container):
    """
    Renders document scan status classification UI breakdown.
    """
    scan_lines = ["**Scanning uploaded documents...**\n"]
    for path, info in analysis.items():
        icon = info["icon"]
        label = info["label"]
        filename = os.path.basename(path)
        scan_lines.append(f"{icon} `{filename}` ({label})")
    container.markdown("\n\n".join(scan_lines))


def execute_incremental_processing(pdf_paths, excel_paths, csv_paths, status_container):
    """
    Orchestrates scan analysis, progress feedback, and incremental indexing execution.
    """
    progress_bar = status_container.progress(0, text="Scanning uploaded documents...")
    scan_box = status_container.empty()

    all_target_files = pdf_paths + excel_paths + csv_paths
    stored_meta = load_doc_metadata()
    analysis = analyze_document_changes(all_target_files, stored_meta)
    render_scan_analysis(analysis, scan_box)

    def update_stage(percentage: float, message: str):
        progress_bar.progress(percentage, text=message)

    vs, final_analysis = process_incremental_indexing(
        pdf_paths,
        excel_paths,
        csv_paths,
        progress_callback=update_stage
    )

    # Clear cached chatbot resource so new index is picked up
    load_chatbot.clear()
    if "agent" in st.session_state:
        del st.session_state["agent"]

    return vs


# ====================================================
# SMART STARTUP & BACKGROUND LOADING ENGINE
# ====================================================
current_hashes = get_document_hashes(all_active_files) if all_active_files else {}
saved_hashes = load_saved_hashes()
index_exists = os.path.exists("faiss_index")
is_valid, validation_reason = validate_faiss_index("faiss_index") if index_exists else (False, "Index folder missing")

startup_status_placeholder = st.empty()
vectorstore_ready = False
loaded_vs = None
load_time_seconds = None

if process_btn:
    try:
        startup_status_placeholder.empty()
        proc_container = st.empty()

        if is_valid and not has_documents_changed(current_hashes, saved_hashes):
            start_t = time.perf_counter()
            load_faiss_index("faiss_index")
            end_t = time.perf_counter()
            elapsed = round(end_t - start_t, 2)
            st.sidebar.success(f"⚡ Loaded existing FAISS index in {elapsed:.2f} seconds!\nChatbot is ready.")
            vectorstore_ready = True
        else:
            execute_incremental_processing(pdf_files, excel_files, csv_files, proc_container)
            st.sidebar.success("✅ Documents processed successfully!\nChatbot is now ready.")
            vectorstore_ready = True

    except Exception as e:
        st.sidebar.error(f"❌ An error occurred during processing: {str(e)}")

elif index_exists and is_valid and all_active_files:
    if not has_documents_changed(current_hashes, saved_hashes):
        # Scenario 1: FAISS index exists & uploaded documents unchanged -> Auto Load
        start_t = time.perf_counter()
        loaded_vs = load_faiss_index("faiss_index")
        end_t = time.perf_counter()
        load_time_seconds = round(end_t - start_t, 2)

        if loaded_vs is not None:
            vectorstore_ready = True
            startup_status_placeholder.markdown(f"""
            <div style="background-color: #d4edda; color: #155724; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong>✅ Vector Database Found</strong><br>
                ⚡ Loaded existing FAISS index for <strong>{len(all_active_files)} uploaded document(s)</strong> in <strong>{load_time_seconds:.2f} seconds</strong><br>
                🤖 <strong>Chatbot Ready</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Auto Recovery: load failed despite validation -> trigger rebuild
            startup_status_placeholder.warning("⚠ Could not load existing vector database. Rebuilding...")
            safe_clean_index("faiss_index")
            try:
                execute_incremental_processing(pdf_files, excel_files, csv_files, startup_status_placeholder)
                vectorstore_ready = True
            except Exception as e:
                st.error(f"❌ Rebuild failed: {str(e)}")
    else:
        # Scenario 3: Document updates detected -> Auto process delta
        startup_status_placeholder.warning("🔄 Document updates detected. Processing incremental indexing...")
        try:
            execute_incremental_processing(pdf_files, excel_files, csv_files, startup_status_placeholder)
            vectorstore_ready = True
            startup_status_placeholder.success("✅ Vector database updated incrementally.\n\n🤖 Chatbot Ready.")
        except Exception as e:
            st.error(f"❌ Incremental update failed: {str(e)}")
elif index_exists and not is_valid and all_active_files:
    # Feature: Auto Recovery / Validation failure
    startup_status_placeholder.warning(f"⚠ Existing vector database is invalid ({validation_reason}). Rebuilding...")
    safe_clean_index("faiss_index")
    try:
        execute_incremental_processing(pdf_files, excel_files, csv_files, startup_status_placeholder)
        vectorstore_ready = True
        startup_status_placeholder.success("✅ Vector database rebuilt successfully.\n\n🤖 Chatbot Ready.")
    except Exception as e:
        st.error(f"❌ Rebuild failed: {str(e)}")
elif not all_active_files:
    startup_status_placeholder.info("ℹ Please upload one or more financial documents in the sidebar to get started.")
else:
    startup_status_placeholder.info("ℹ Documents uploaded. Please click **Process Documents** in the sidebar to index your data files.")

# Render System Status indicators in sidebar
with st.sidebar:
    gemini_key_present = bool(os.getenv("GOOGLE_API_KEY"))
    gemini_status = "🟢 Gemini Connected" if gemini_key_present else "🔴 Gemini API Key Missing"
    faiss_status = "🟢 FAISS Loaded" if vectorstore_ready else "🔴 FAISS Not Loaded"
    docs_status = "🟢 Documents Indexed" if vectorstore_ready else "🟡 Indexing Required"
    chat_status = "🟢 Ready for Chat" if vectorstore_ready else "🔴 Action Required"

    st.markdown(f"""
- {gemini_status}
- {faiss_status}
- {docs_status}
- {chat_status}
""")

    if vectorstore_ready:
        meta = load_index_metadata()
        if not meta and loaded_vs is not None:
            # Auto-generate metadata if loading pre-existing index
            chunk_cnt = loaded_vs.index.ntotal if hasattr(loaded_vs, 'index') else "N/A"
            meta = {
                "num_documents": len(all_active_files),
                "num_chunks": chunk_cnt,
                "last_updated": datetime.now().strftime("%d %b %Y %I:%M %p")
            }
            save_index_metadata(meta)

        num_docs = meta.get("num_documents", len(all_active_files))
        num_chunks = meta.get("num_chunks", "N/A")
        last_updated = meta.get("last_updated", "N/A")

        st.markdown(f"""
**Indexed Documents:** {num_docs}  
**Vector Chunks:** {num_chunks}  
**Last Updated:**  
{last_updated}
""")
    st.markdown("---")

# ====================================================
# CHAT INTERFACE
# ====================================================
if vectorstore_ready:
    # Load agent once per session (cached via @st.cache_resource)
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
                        st.download_button(
                            label=btn_label,
                            data=f,
                            file_name=os.path.basename(file_path),
                            key=f"dl_{msg['content'][:10]}"
                        )

    # React to user input when input is given
    if prompt := st.chat_input("Ask a financial question or request a report...", disabled=False):
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
                            st.download_button(
                                label=btn_label,
                                data=f,
                                file_name=os.path.basename(file_path),
                                key="dl_new"
                            )

                # Save to memory
                msg_data = {"role": "assistant", "content": answer}
                if file_path:
                    msg_data["file_path"] = file_path
                st.session_state.messages.append(msg_data)

                st.session_state.chat_history.append(HumanMessage(content=prompt))
                st.session_state.chat_history.append(AIMessage(content=answer))

else:
    st.chat_input("Please upload and process documents to enable chat...", disabled=True)
