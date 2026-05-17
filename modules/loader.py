from langchain_community.document_loaders import PyPDFLoader
import pandas as pd
from langchain_core.documents import Document
import os


def load_pdfs(pdf_paths):
    documents = []

    for path in pdf_paths:
        loader = PyPDFLoader(path)
        docs = loader.load()

        for doc in docs:
            doc.metadata["source"] = os.path.basename(path)

        documents.extend(docs)

    return documents


def load_excel(excel_path):
    df = pd.read_excel(excel_path)

    text = df.to_string(index=False)

    return [
        Document(
            page_content=text,
            metadata={"source": os.path.basename(excel_path)}
        )
    ]


def load_csv(csv_path):
    df = pd.read_csv(csv_path)

    text = df.to_string(index=False)

    return [
        Document(
            page_content=text,
            metadata={"source": os.path.basename(csv_path)}
        )
    ]