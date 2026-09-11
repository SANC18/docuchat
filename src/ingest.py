"""
Ingestion pipeline for DocuChat.

Flow:
    PDF files in /data
        -> extract raw text (pypdf)
        -> split into overlapping chunks (RecursiveCharacterTextSplitter)
        -> embed each chunk (local sentence-transformers model, no API cost)
        -> store vectors in a FAISS index on disk

Run directly to (re)build the index from everything in /data:
    python -m src.ingest
"""

import os
import sys

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from src import config


def load_documents(data_dir: str = config.DATA_DIR):
    """Load every PDF in data_dir into LangChain Document objects."""
    documents = []
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in '{data_dir}'. Add at least one PDF and re-run.")
        sys.exit(1)

    for filename in pdf_files:
        path = os.path.join(data_dir, filename)
        loader = PyPDFLoader(path)
        pages = loader.load()  # one Document per page, with page metadata attached
        documents.extend(pages)
        print(f"Loaded '{filename}' ({len(pages)} pages)")

    return documents


def split_documents(documents):
    """Break long documents into overlapping chunks sized for retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
    return chunks


def build_vectorstore(chunks):
    """Embed chunks locally and persist a FAISS index to disk."""
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    os.makedirs(config.VECTORSTORE_DIR, exist_ok=True)
    vectorstore.save_local(config.VECTORSTORE_DIR)
    print(f"Saved FAISS index to '{config.VECTORSTORE_DIR}'")
    return vectorstore


def run():
    documents = load_documents()
    chunks = split_documents(documents)
    build_vectorstore(chunks)
    print("Ingestion complete. You can now run the app with: python app.py")


if __name__ == "__main__":
    run()
