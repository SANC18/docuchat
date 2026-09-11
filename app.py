"""
DocuChat — Flask entry point.

Routes:
    GET  /                -> chat UI
    POST /api/chat        -> {"question": "..."} -> {"answer": "...", "sources": [...]}
    POST /api/upload      -> multipart PDF upload -> re-runs ingestion, adds file to the index
    GET  /api/health      -> simple liveness check
"""

import os
from flask import Flask, request, jsonify, render_template

from src import config
from src import rag
from src.ingest import load_documents, split_documents, build_vectorstore

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Field 'question' is required."}), 400

    try:
        answer, sources = rag.answer_question(question)
        return jsonify({"answer": answer, "sources": sources})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:  # pragma: no cover - defensive catch-all for the API layer
        return jsonify({"error": f"Unexpected error: {e}"}), 500


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part named 'file' in the request."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    os.makedirs(config.DATA_DIR, exist_ok=True)
    save_path = os.path.join(config.DATA_DIR, file.filename)
    file.save(save_path)

    # Rebuild the index over everything currently in /data.
    # For a larger app you'd append incrementally instead of rebuilding from scratch.
    documents = load_documents()
    chunks = split_documents(documents)
    build_vectorstore(chunks)
    rag._vectorstore = None  # force reload on next query

    return jsonify({"message": f"'{file.filename}' ingested successfully."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
