"""
Lightweight sanity tests that don't require an API key or a real PDF.
Run with: pytest
"""

from langchain_core.documents import Document
from src.ingest import split_documents
from src import config


def test_split_documents_respects_chunk_size():
    long_text = "sentence. " * 500  # ~5000 characters
    docs = [Document(page_content=long_text, metadata={"source": "fake.pdf", "page": 0})]

    chunks = split_documents(docs)

    assert len(chunks) > 1
    # allow a little slack over chunk_size since the splitter breaks on separators, not mid-word
    assert all(len(c.page_content) <= config.CHUNK_SIZE + 200 for c in chunks)


def test_split_documents_preserves_metadata():
    docs = [Document(page_content="short text", metadata={"source": "fake.pdf", "page": 3})]
    chunks = split_documents(docs)

    assert chunks[0].metadata["source"] == "fake.pdf"
    assert chunks[0].metadata["page"] == 3
