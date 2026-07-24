import os
import time
from datetime import datetime
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from modules.loader import load_pdfs, load_excel, load_csv
from modules.utils import (
    save_index_metadata,
    validate_faiss_index,
    load_doc_metadata,
    save_doc_metadata,
    save_file_hashes,
    calculate_file_hash,
    get_file_mtime,
    analyze_document_changes,
)


@st.cache_resource(show_spinner=False)
def get_embeddings():
    """
    Initializes and caches the local HuggingFace embedding model.
    Using @st.cache_resource prevents reloading the model on every run.
    """
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


@st.cache_resource(show_spinner=False)
def load_faiss_index(index_path: str = "faiss_index"):
    """
    Loads and caches the existing FAISS vector store index from disk after performing validation checks.
    """
    is_valid, reason = validate_faiss_index(index_path)
    if not is_valid:
        return None

    try:
        embeddings = get_embeddings()
        return FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception:
        return None


def create_vector_store(documents, progress_callback=None):
    """
    Full build: Splits documents into chunks, generates embeddings with IDs, builds and saves FAISS vector store along with metadata.
    Accepts an optional progress_callback(percentage: float, message: str) to report progress.
    """
    def update_progress(percent, text):
        if progress_callback:
            progress_callback(percent, text)

    # Step 3: Chunking documents
    update_progress(0.55, "✂ Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_docs = splitter.split_documents(documents)

    # Assign IDs per chunk
    doc_chunk_map = {}
    chunk_ids = []
    for idx, doc in enumerate(split_docs):
        src = doc.metadata.get("source", "unknown")
        cid = f"{src}_chunk_{idx}"
        chunk_ids.append(cid)
        if src not in doc_chunk_map:
            doc_chunk_map[src] = []
        doc_chunk_map[src].append(cid)

    # Step 4: Generating embeddings
    update_progress(0.75, "🧠 Generating embeddings...")
    embeddings = get_embeddings()

    # Step 5: Creating FAISS Vector Store
    update_progress(0.90, f"📚 Creating FAISS Vector Store for {len(split_docs)} chunks...")
    vectorstore = FAISS.from_documents(
        split_docs,
        embeddings,
        ids=chunk_ids
    )

    # Step 6: Saving Vector Database
    update_progress(0.95, "💾 Saving Vector Database...")
    vectorstore.save_local("faiss_index")

    # Build per-document metadata
    doc_metadata_records = {}
    timestamp = datetime.now().strftime("%d %b %Y %I:%M %p")

    # Group original documents by source filename
    for doc in documents:
        src = doc.metadata.get("source", "")
        if src and src not in doc_metadata_records:
            full_path = src
            c_ids = doc_chunk_map.get(src, [])
            doc_metadata_records[full_path] = {
                "file_name": full_path,
                "hash": calculate_file_hash(full_path) if os.path.exists(full_path) else "",
                "last_modified": get_file_mtime(full_path) if os.path.exists(full_path) else 0.0,
                "num_chunks": len(c_ids),
                "chunk_ids": c_ids,
                "status": "indexed",
                "indexed_timestamp": timestamp
            }

    doc_meta_payload = {"documents": doc_metadata_records}
    save_doc_metadata(doc_meta_payload)

    # Save summary metadata
    unique_sources = set(doc.metadata.get("source", "") for doc in documents if doc.metadata.get("source"))
    metadata = {
        "num_documents": len(unique_sources) if unique_sources else len(documents),
        "num_chunks": len(split_docs),
        "last_updated": timestamp
    }
    save_index_metadata(metadata)

    # Clear cached FAISS index
    load_faiss_index.clear()

    return vectorstore


def process_incremental_indexing(pdf_files: list, excel_files: list, csv_files: list, progress_callback=None):
    """
    Performs incremental document indexing (delta processing).
    Accepts lists of pdf_files, excel_files, and csv_files.
    Classifies documents into new, modified, unchanged, and deleted,
    and updates FAISS vector store without re-embedding unchanged documents.
    """
    def update_progress(percent, text):
        if progress_callback:
            progress_callback(percent, text)

    # Handle string or list arguments gracefully
    if isinstance(excel_files, str):
        excel_files = [excel_files] if excel_files else []
    if isinstance(csv_files, str):
        csv_files = [csv_files] if csv_files else []

    all_target_files = pdf_files + excel_files + csv_files
    stored_doc_meta = load_doc_metadata()
    docs_records = stored_doc_meta.get("documents", {})

    # Analyze changes
    analysis = analyze_document_changes(all_target_files, stored_doc_meta)

    new_files = [f for f, info in analysis.items() if info["status"] == "new"]
    modified_files = [f for f, info in analysis.items() if info["status"] == "modified"]
    unchanged_files = [f for f, info in analysis.items() if info["status"] == "unchanged"]
    deleted_files = [f for f, info in analysis.items() if info["status"] == "deleted"]

    index_exists = os.path.exists("faiss_index")
    is_valid, _ = validate_faiss_index("faiss_index") if index_exists else (False, "")

    # Scenario: If no index exists OR deleted files exist -> Full build required
    if not is_valid or len(deleted_files) > 0 or not docs_records:
        update_progress(0.15, "🔄 Building FAISS Index for uploaded documents...")
        all_docs = []
        if pdf_files:
            update_progress(0.25, f"📄 Loading {len(pdf_files)} PDF document(s)...")
            all_docs.extend(load_pdfs(pdf_files))
        for xf in excel_files:
            update_progress(0.40, f"📊 Reading Excel file: {os.path.basename(xf)}...")
            all_docs.extend(load_excel(xf))
        for cf in csv_files:
            update_progress(0.45, f"📈 Reading CSV file: {os.path.basename(cf)}...")
            all_docs.extend(load_csv(cf))

        vs = create_vector_store(all_docs, progress_callback=progress_callback)

        # Update hashes
        hashes = {f: calculate_file_hash(f) for f in all_target_files if os.path.exists(f)}
        save_file_hashes(hashes)
        return vs, analysis

    # Scenario: If everything is unchanged -> Skip processing
    if len(new_files) == 0 and len(modified_files) == 0:
        update_progress(1.00, "✓ All documents are up to date. Using cached FAISS index.")
        vs = load_faiss_index("faiss_index")
        return vs, analysis

    # Scenario: Incremental update (new and/or modified files exist, no deletion)
    update_progress(0.30, f"⚡ Incremental update: {len(new_files)} new, {len(modified_files)} modified file(s)...")

    vs = load_faiss_index("faiss_index")
    if vs is None:
        # Fallback to rebuild if load fails
        return process_incremental_indexing(pdf_files, excel_files, csv_files, progress_callback=progress_callback)

    embeddings = get_embeddings()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    timestamp = datetime.now().strftime("%d %b %Y %I:%M %p")

    # 1. Remove old vectors for modified files
    for mod_file in modified_files:
        if mod_file in docs_records:
            old_cids = docs_records[mod_file].get("chunk_ids", [])
            if old_cids:
                try:
                    vs.delete(ids=old_cids)
                except Exception:
                    pass
            del docs_records[mod_file]

    # 2. Process modified and new files
    files_to_process = modified_files + new_files
    for target_file in files_to_process:
        update_progress(0.60, f"⏳ Processing {os.path.basename(target_file)}...")
        raw_docs = []
        ext = target_file.lower().split(".")[-1]
        if ext == "pdf":
            raw_docs = load_pdfs([target_file])
        elif ext in ["xls", "xlsx"]:
            raw_docs = load_excel(target_file)
        elif ext == "csv":
            raw_docs = load_csv(target_file)

        if not raw_docs:
            continue

        split_docs = splitter.split_documents(raw_docs)
        cids = [f"{target_file}_chunk_{i}_{int(time.time())}" for i in range(len(split_docs))]

        # Add vectors to existing index
        vs.add_documents(split_docs, ids=cids)

        # Update metadata record
        docs_records[target_file] = {
            "file_name": target_file,
            "hash": calculate_file_hash(target_file),
            "last_modified": get_file_mtime(target_file),
            "num_chunks": len(split_docs),
            "chunk_ids": cids,
            "status": "indexed",
            "indexed_timestamp": timestamp
        }

    # 3. Save updated index and metadata
    update_progress(0.90, "💾 Saving updated FAISS Index and metadata...")
    vs.save_local("faiss_index")

    stored_doc_meta["documents"] = docs_records
    save_doc_metadata(stored_doc_meta)

    # Save summary metadata
    hashes = {f: calculate_file_hash(f) for f in all_target_files if os.path.exists(f)}
    save_file_hashes(hashes)

    total_chunks = sum(rec.get("num_chunks", 0) for rec in docs_records.values())
    summary_meta = {
        "num_documents": len(all_target_files),
        "num_chunks": total_chunks if total_chunks > 0 else vs.index.ntotal,
        "last_updated": timestamp
    }
    save_index_metadata(summary_meta)

    load_faiss_index.clear()
    update_progress(1.00, "✅ Incremental indexing complete! Chatbot ready.")

    return vs, analysis