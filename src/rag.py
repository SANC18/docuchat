"""
Retrieval-Augmented Generation logic for DocuChat.

Given a user question:
  1. Embed the question with the same local embedding model used at ingest time.
  2. Retrieve the top-K most similar chunks from the FAISS index.
  3. Stuff those chunks into a prompt as grounding context.
  4. Ask Claude to answer using ONLY that context, citing which source chunk it used.
"""

import os
import anthropic

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from src import config

_vectorstore = None  # lazy-loaded singleton so we don't reload the index on every request


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        if not os.path.exists(config.VECTORSTORE_DIR):
            raise FileNotFoundError(
                "No vectorstore found. Run 'python -m src.ingest' first to build the index."
            )
        embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
        _vectorstore = FAISS.load_local(
            config.VECTORSTORE_DIR,
            embeddings,
            allow_dangerous_deserialization=True,  # safe here: it's our own locally-generated index
        )
    return _vectorstore


def retrieve_chunks(question: str, k: int = config.TOP_K):
    """Return the k most relevant chunks (with metadata) for a question."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(question, k=k)
    return results


def build_prompt(question: str, chunks) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", "?")
        context_blocks.append(
            f"[Source {i} | file: {os.path.basename(source)} | page: {page}]\n{chunk.page_content}"
        )
    context_text = "\n\n".join(context_blocks)

    return f"""You are a helpful assistant answering questions using ONLY the context below.
If the answer isn't contained in the context, say so honestly instead of guessing.
When you use information from a source, mention its number, e.g. (Source 2).

Context:
{context_text}

Question: {question}

Answer:"""


def ask_claude(prompt: str) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file (see .env.example)."
        )
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def answer_question(question: str):
    """End-to-end: retrieve -> prompt -> generate. Returns (answer, sources)."""
    chunks = retrieve_chunks(question)
    prompt = build_prompt(question, chunks)
    answer = ask_claude(prompt)

    sources = [
        {
            "file": os.path.basename(c.metadata.get("source", "unknown")),
            "page": c.metadata.get("page", "?"),
            "snippet": c.page_content[:200].strip() + "...",
        }
        for c in chunks
    ]
    return answer, sources
