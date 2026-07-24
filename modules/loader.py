import os
import pandas as pd
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


@st.cache_data(show_spinner=False)
def load_pdfs(pdf_paths):
    """
    Loads PDF documents from the given list of file paths.
    Cached with @st.cache_data to prevent redundant disk reading.
    """
    documents = []
    # Ensure list is iterable even if tuple passed
    for path in pdf_paths:
        if os.path.exists(path):
            loader = PyPDFLoader(path)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = os.path.basename(path)
            documents.extend(docs)
    return documents


@st.cache_data(show_spinner=False)
def load_excel(excel_path):
    """
    Loads an Excel file as a LangChain Document.
    Cached with @st.cache_data to prevent redundant disk reading.
    """
    if not os.path.exists(excel_path):
        return []
    df = pd.read_excel(excel_path)
    text = df.to_string(index=False)
    return [
        Document(
            page_content=text,
            metadata={"source": os.path.basename(excel_path)}
        )
    ]


@st.cache_data(show_spinner=False)
def load_csv(csv_path):
    """
    Loads a CSV file as a LangChain Document.
    Cached with @st.cache_data to prevent redundant disk reading.
    """
    if not os.path.exists(csv_path):
        return []
    df = pd.read_csv(csv_path)
    text = df.to_string(index=False)
    return [
        Document(
            page_content=text,
            metadata={"source": os.path.basename(csv_path)}
        )
    ]