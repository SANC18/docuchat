"""
Central configuration for DocuChat.
All tunable values live here so the rest of the code never hardcodes paths or magic numbers.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present

# --- API keys / model settings ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# --- Embedding model (runs locally, no API key needed) ---
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# --- Storage paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")

# --- Chunking strategy ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))       # characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))  # overlap between chunks

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))  # number of chunks retrieved per question
