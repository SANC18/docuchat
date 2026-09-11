# 📄 DocuChat — RAG-based PDF Question Answering Assistant

DocuChat lets you upload PDF documents and ask natural-language questions about them.
It uses **Retrieval-Augmented Generation (RAG)**: instead of relying on an LLM's memorized
knowledge (which can be outdated or wrong), it retrieves the most relevant passages from
your own documents and grounds the model's answer in that retrieved text — with citations
back to the source page.

## Why RAG?

Large language models don't know about your private documents, and they can hallucinate
facts. RAG fixes this by:
1. Splitting your documents into small chunks.
2. Turning each chunk into a vector (an "embedding") that captures its meaning.
3. Storing those vectors in a searchable index (FAISS).
4. At question time, embedding the question, finding the most *semantically similar*
   chunks, and handing only those chunks to the LLM as context.

This is the same core pattern behind most production "chat with your data" tools.

## Architecture

```
                 ┌──────────────┐
   PDF files --->│   ingest.py   │---> chunks ---> embeddings ---> FAISS index (vectorstore/)
                 └──────────────┘

                 ┌──────────────┐        ┌───────────────┐
   Question ---->│    rag.py     │------->│  Claude (LLM)  │---> Answer + Sources
                 │ (retrieval)   │        └───────────────┘
                 └──────────────┘
                        ▲
                        │ FAISS similarity search
                        │
                 vectorstore/ (built once, reused on every query)
```

**Flask (`app.py`)** exposes this pipeline as a small REST API and a simple browser chat UI.

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude (Anthropic API) | High-quality generation; you already hold Anthropic certifications |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, free) | No API cost for embedding; runs on CPU |
| Vector store | FAISS | Fast, simple, no external database needed |
| Orchestration | LangChain | Standard tooling for loaders/splitters/vectorstores |
| Backend | Flask | Lightweight REST API, matches your existing stack |
| Deployment | Docker | Reproducible, one-command run |

## Project Structure

```
docuchat/
├── app.py                  # Flask app: routes + chat UI
├── src/
│   ├── config.py           # all settings in one place
│   ├── ingest.py           # PDF -> chunks -> embeddings -> FAISS index
│   └── rag.py               # retrieval + prompt construction + Claude call
├── templates/index.html    # chat UI page
├── static/style.css        # UI styling
├── static/app.js           # UI frontend logic (fetch calls to the API)
├── data/                   # put your PDFs here
├── vectorstore/            # generated FAISS index (not committed)
├── tests/test_ingest.py    # sanity tests for the chunking logic
├── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
```

## Setup

1. **Clone and install dependencies**
   ```bash
   git clone https://github.com/SANC18/docuchat.git
   cd docuchat
   python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Add your API key**
   ```bash
   cp .env.example .env
   # edit .env and paste your ANTHROPIC_API_KEY
   ```
   Get a key from [console.anthropic.com](https://console.anthropic.com/).

3. **Add a PDF and build the index**
   ```bash
   cp /path/to/your/document.pdf data/
   python -m src.ingest
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` and start asking questions. You can also upload new PDFs
   directly from the UI — it re-ingests automatically.

## REST API

| Method | Route | Body | Description |
|---|---|---|---|
| POST | `/api/chat` | `{"question": "..."}` | Returns `{"answer": "...", "sources": [...]}` |
| POST | `/api/upload` | multipart `file` (PDF) | Ingests a new PDF into the index |
| GET | `/api/health` | — | Liveness check |

Example:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main conclusion of this document?"}'
```

## Run with Docker

```bash
docker build -t docuchat .
docker run -p 5000:5000 --env-file .env -v $(pwd)/data:/app/data -v $(pwd)/vectorstore:/app/vectorstore docuchat
```

## Running Tests

```bash
pip install pytest
pytest
```

## Possible Extensions (good next steps)

- Swap FAISS for a persistent vector DB (Pinecone, Chroma, Qdrant) for larger document sets.
- Add conversation memory so follow-up questions use chat history as extra context.
- Support more file types (`.docx`, `.txt`, web pages) via additional LangChain loaders.
- Add a re-ranking step (e.g. cross-encoder) after retrieval to improve answer quality.
- Stream the Claude response token-by-token to the UI instead of waiting for the full answer.

## License

MIT
