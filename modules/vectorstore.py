import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st


def create_vector_store(documents):
    # Optional: progress indicator
    try:
        progress_bar = st.progress(0, text="Splitting documents into chunks...")
        has_st = True
    except:
        has_st = False

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = splitter.split_documents(documents)

    if has_st:
        progress_bar.progress(0.2, text="Loading local embedding model (fast, no rate limits)...")

    # Use a fast local model, e.g., all-MiniLM-L6-v2
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    if has_st:
        progress_bar.progress(0.6, text=f"Creating Vector Index for {len(split_docs)} chunks...")

    # No need for batching/sleep because we are running locally without API limits!
    vectorstore = FAISS.from_documents(
        split_docs,
        embeddings
    )

    if has_st:
        progress_bar.progress(0.9, text="Saving Vector Index...")

    vectorstore.save_local("faiss_index")

    if has_st:
        progress_bar.empty()

    return vectorstore
