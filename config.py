from pathlib import Path
import os

# === Base Paths ===
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "documents"
PDF_DIR = BASE_DIR / "pdfs"
MODEL_DIR = BASE_DIR / "tmp_model"

# Make sure the runtime folders exist before anything mounts or writes to them.
for _d in (UPLOAD_DIR, PDF_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# === ChromaDB ===
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "default_collection"

# === Embedding Model ===
# One model is used for everything (storage, search and chunking).
# It is downloaded once into MODEL_DIR (see download_model.py) and loaded
# from there afterwards, so the app works fully offline.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LOCAL_MODEL_PATH = MODEL_DIR

# === Chunking ===
DEFAULT_CHUNKING_METHOD = "graph-pagerank"
UPLOAD_CHUNKING_METHOD = os.getenv("UPLOAD_CHUNKING_METHOD", "graph")
CHUNKING_METHOD_OPTIONS = ["sentences", "semantics", "graph", "paragraphs", "dynamic", "graph-pagerank"]
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt"}

# === Ollama ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
