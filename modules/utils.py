import os
import json
import hashlib
import shutil
from datetime import datetime
import streamlit as st

HASH_FILE_PATH = os.path.join("faiss_index", "file_hashes.json")
METADATA_FILE_PATH = os.path.join("faiss_index", "metadata.json")
DOC_METADATA_FILE = os.path.join("faiss_index", "doc_metadata.json")
UPLOAD_DIR = "uploads"


def format_file_size(size_bytes: int) -> str:
    """
    Formats byte size into readable KB or MB string.
    """
    if size_bytes <= 0:
        return "0 KB"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_or_create_session_dir(base_dir: str = UPLOAD_DIR) -> str:
    """
    Generates or retrieves a unique session-based folder under uploads/ (e.g. uploads/session_20260724_234818).
    """
    os.makedirs(base_dir, exist_ok=True)
    if "session_dir" not in st.session_state or not st.session_state["session_dir"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s_dir = os.path.join(base_dir, f"session_{timestamp}")
        os.makedirs(s_dir, exist_ok=True)
        st.session_state["session_dir"] = s_dir
    return st.session_state["session_dir"]


def save_session_uploaded_files(uploaded_files, session_dir: str) -> tuple:
    """
    Saves uploaded files into the active session folder, filtering empty files and calculating total byte size.
    Returns (saved_file_paths, total_bytes).
    """
    os.makedirs(session_dir, exist_ok=True)
    saved_paths = []
    total_bytes = 0

    for file in uploaded_files:
        content = file.getbuffer()
        fsize = len(content)
        # Skip 0-byte empty files
        if fsize == 0:
            continue

        filepath = os.path.join(session_dir, file.name)
        with open(filepath, "wb") as f:
            f.write(content)

        saved_paths.append(filepath)
        total_bytes += fsize

    return saved_paths, total_bytes


def get_session_active_files(session_dir: str) -> tuple:
    """
    Scans the given session directory and categorizes valid files into (pdfs, excels, csvs, total_bytes).
    """
    if not session_dir or not os.path.exists(session_dir):
        return [], [], [], 0

    pdfs, excels, csvs = [], [], []
    total_bytes = 0

    for fname in os.listdir(session_dir):
        full_path = os.path.join(session_dir, fname)
        if os.path.isfile(full_path):
            fsize = os.path.getsize(full_path)
            if fsize == 0:
                continue

            total_bytes += fsize
            ext = fname.lower().split(".")[-1]
            if ext == "pdf":
                pdfs.append(full_path)
            elif ext in ["xls", "xlsx"]:
                excels.append(full_path)
            elif ext == "csv":
                csvs.append(full_path)

    return pdfs, excels, csvs, total_bytes


def save_uploaded_files(uploaded_files, upload_dir: str = UPLOAD_DIR) -> list:
    """
    Legacy helper: saves uploaded files into a folder.
    """
    os.makedirs(upload_dir, exist_ok=True)
    saved_paths = []
    for file in uploaded_files:
        filepath = os.path.join(upload_dir, file.name)
        with open(filepath, "wb") as f:
            f.write(file.getbuffer())
        saved_paths.append(filepath)
    return saved_paths


def get_active_upload_files(upload_dir: str = UPLOAD_DIR) -> tuple:
    """
    Legacy helper: scans upload folder.
    """
    pdfs, excels, csvs, _ = get_session_active_files(upload_dir)
    return pdfs, excels, csvs


def calculate_file_hash(filepath: str) -> str:
    """
    Computes the SHA-256 hash of a file reading in chunks.
    """
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_mtime(filepath: str) -> float:
    """
    Returns last modified timestamp of a file.
    """
    if os.path.exists(filepath):
        return os.path.getmtime(filepath)
    return 0.0


def get_document_hashes(file_paths: list) -> dict:
    """
    Generates a dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    for path in file_paths:
        if os.path.exists(path):
            hashes[path] = calculate_file_hash(path)
    return hashes


def load_saved_hashes(hash_file_path: str = HASH_FILE_PATH) -> dict:
    """
    Loads saved document SHA-256 hashes from a JSON file.
    Returns an empty dict if the file does not exist or fails to parse.
    """
    if os.path.exists(hash_file_path):
        try:
            with open(hash_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_file_hashes(hashes: dict, hash_file_path: str = HASH_FILE_PATH) -> None:
    """
    Saves document SHA-256 hashes to a JSON file.
    """
    os.makedirs(os.path.dirname(hash_file_path), exist_ok=True)
    with open(hash_file_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)


def has_documents_changed(current_hashes: dict, saved_hashes: dict) -> bool:
    """
    Compares current file hashes against previously saved hashes.
    Returns True if any file has changed, added, or removed.
    """
    if not saved_hashes or not current_hashes:
        return True
    return current_hashes != saved_hashes


def save_index_metadata(metadata: dict, metadata_path: str = METADATA_FILE_PATH) -> None:
    """
    Saves index metadata (document count, chunk count, last updated timestamp) to JSON.
    """
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def load_index_metadata(metadata_path: str = METADATA_FILE_PATH) -> dict:
    """
    Loads index metadata from JSON file. Returns empty dict if file does not exist or fails to parse.
    """
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def load_doc_metadata(filepath: str = DOC_METADATA_FILE) -> dict:
    """
    Loads detailed per-document metadata dictionary from JSON.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_doc_metadata(doc_metadata: dict, filepath: str = DOC_METADATA_FILE) -> None:
    """
    Saves detailed per-document metadata dictionary to JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc_metadata, f, indent=2)


def analyze_document_changes(target_files: list, stored_doc_metadata: dict) -> dict:
    """
    Compares target files against stored metadata and classifies each as:
    'new', 'modified', 'unchanged', or 'deleted'.
    """
    analysis = {}
    docs_meta = stored_doc_metadata.get("documents", {})

    for path in target_files:
        curr_hash = calculate_file_hash(path)
        curr_mtime = get_file_mtime(path)

        if path not in docs_meta:
            analysis[path] = {
                "status": "new",
                "icon": "➕",
                "label": "new",
                "hash": curr_hash,
                "mtime": curr_mtime
            }
        elif docs_meta[path].get("hash") != curr_hash:
            analysis[path] = {
                "status": "modified",
                "icon": "🔄",
                "label": "modified",
                "hash": curr_hash,
                "mtime": curr_mtime
            }
        else:
            analysis[path] = {
                "status": "unchanged",
                "icon": "✓",
                "label": "unchanged",
                "hash": curr_hash,
                "mtime": curr_mtime
            }

    # Check for deleted files
    for stored_path in docs_meta.keys():
        if stored_path not in target_files:
            analysis[stored_path] = {
                "status": "deleted",
                "icon": "🗑",
                "label": "removed",
                "hash": docs_meta[stored_path].get("hash", ""),
                "mtime": 0.0
            }

    return analysis


def validate_faiss_index(index_path: str = "faiss_index") -> tuple:
    """
    Performs comprehensive startup validation on the FAISS index folder.
    Checks existence of folder, index files, file hashes, and metadata readability.
    Returns (is_valid: bool, reason: str).
    """
    if not os.path.exists(index_path) or not os.path.isdir(index_path):
        return False, "Index folder does not exist."

    index_file = os.path.join(index_path, "index.faiss")
    pkl_file = os.path.join(index_path, "index.pkl")
    hashes_file = os.path.join(index_path, "file_hashes.json")

    if not os.path.exists(index_file):
        return False, "index.faiss is missing."
    if not os.path.exists(pkl_file):
        return False, "index.pkl is missing."
    if not os.path.exists(hashes_file):
        return False, "file_hashes.json is missing."

    # Validate file hashes readability
    try:
        with open(hashes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return False, "file_hashes.json format is invalid."
    except Exception as e:
        return False, f"file_hashes.json is corrupted: {str(e)}"

    # Validate file non-zero size
    if os.path.getsize(index_file) == 0 or os.path.getsize(pkl_file) == 0:
        return False, "Index files are empty (0 bytes)."

    return True, "FAISS index is valid."


def safe_clean_index(index_path: str = "faiss_index") -> None:
    """
    Safely deletes the invalid or corrupted FAISS index folder.
    """
    if os.path.exists(index_path):
        try:
            shutil.rmtree(index_path)
        except Exception:
            pass
