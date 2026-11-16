# Deployable-Knowledge (R1)

**Offline-first RAG system for tactical and edge environments**

> This fork is re-baselined on upstream commit
> [`6729cb1`](https://github.com/sage-bomb/Deployable-Knowledge/commit/6729cb11e2489989914242b86d4073b0675cdaf4)
> (Jul 28 2025) from [sage-bomb/Deployable-Knowledge](https://github.com/sage-bomb/Deployable-Knowledge),
> with fixes so it installs and runs again on Windows, Linux and macOS. See [Changes in R1](#changes-in-r1).

---

## Overview

Deployable-Knowledge is an offline-capable Retrieval-Augmented Generation (RAG) system. You upload PDFs or
text files, they are chunked and embedded into a local ChromaDB vector store, and a local LLM served by
[Ollama](https://ollama.com) answers questions using the most relevant passages. After a one-time setup,
nothing needs internet access.

## Features

- **Document ingestion**: PDF (text-based) and plain-text files, with header/footer stripping
- **Several chunking algorithms**: sentence, semantic, spaCy graph (default for uploads), paragraph,
  dynamic bottom-up merge and PageRank
- **Local vector store**: ChromaDB on disk (`chroma_db/`)
- **Local LLM**: any Ollama model (default `mistral:7b`)
- **Web UI**: streaming chat, document search, per-document on/off toggles, persona editor,
  chat download and re-upload

---

## Requirements

| What | Version | Notes |
|------|---------|-------|
| Python | **3.11 or 3.12** | 3.13+ is not supported by the pinned packages |
| Ollama | any recent | Runs the chat model locally |
| Disk | ~3 GB free | Python packages (PyTorch) + models |
| Git | any | Only needed to clone / contribute |

The first setup needs internet access. After that the app runs fully offline.

---

## Setup and run on Windows

**1. Install the tools** (PowerShell; skip anything you already have):

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
winget install -e --id Ollama.Ollama
```

Close and reopen PowerShell afterwards so the new commands are on your `PATH`.

**2. Get the code and run the one-time setup:**

```powershell
cd C:\
git clone https://github.com/brentlreitzectr-maker/Deployable-Knowledge-R1.git dk
cd dk
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

> **Keep the folder path short** (such as `C:\dk`). PyTorch contains very deep file paths, and unless
> Windows long-path support is enabled, `pip install` fails when the project is nested deep inside
> `Documents` or `OneDrive`. `setup.ps1` checks for this.

This creates `venv\`, installs the Python packages and downloads the embedding model into `tmp_model\`.

**3. Download a chat model** (one time):

```powershell
ollama pull mistral:7b
```

**4. Start the app:**

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Open <http://localhost:8000>. Press `Ctrl+C` in the terminal to stop it.
Use `.\run.ps1 -Port 8080` for another port, or `.\run.ps1 -Reload` while developing.

---

## Setup and run on Linux / macOS

```bash
# Install Python 3.11/3.12, git, make and Ollama with your package manager first
git clone https://github.com/brentlreitzectr-maker/Deployable-Knowledge-R1.git
cd Deployable-Knowledge-R1
make setup                 # venv + packages + embedding model (needs internet once)
ollama pull mistral:7b     # one-time chat model download
make run                   # http://localhost:8000
```

If `python3` is not 3.11/3.12, point the Makefile at the right interpreter: `make setup PYTHON=python3.12`.

### Manual setup (any OS)

```bash
python -m venv venv
# Windows: venv\Scripts\activate     Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python download_model.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## Using the app

1. **Upload** `.pdf` or `.txt` files in the *Document Library* panel. Large PDFs take a while to embed,
   and scanned (image-only) PDFs are rejected because they contain no extractable text.
2. **Chat**: ask a question. The passages used as context appear under *Search Documents*.
3. **Deactivate** a document to exclude it from chat context without deleting it.
4. **Search** runs a plain vector search without the LLM.
5. **Edit Persona** adds extra instructions to every prompt. **Reset LLM** clears the conversation memory.

Bulk ingest: put PDFs in `pdfs/` and `POST /ingest`. They are converted to text in `documents/` and
embedded in the background. Interactive API docs are at <http://localhost:8000/docs>.

---

## Configuration

Set these environment variables before starting the app:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_MODEL` | `mistral:7b` | Chat model (must be pulled with `ollama pull`) |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama endpoint, e.g. on another machine |
| `OLLAMA_TIMEOUT` | `300` | Seconds to wait for Ollama |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model fetched by `download_model.py` |
| `UPLOAD_CHUNKING_METHOD` | `graph` | `sentences`, `semantics`, `graph`, `paragraphs`, `dynamic` or `graph-pagerank` |

Examples:

```powershell
$env:OLLAMA_MODEL = "llama3.1:8b"; .\run.ps1        # Windows
```

```bash
OLLAMA_MODEL=llama3.1:8b make run                    # Linux/macOS
```

If you change `EMBEDDING_MODEL`, delete `tmp_model/` and `chroma_db/`, then run `download_model.py`
again and re-upload your documents. Embeddings from different models can't be mixed.

### Moving to an offline machine

After setup on a connected machine, copy the whole folder, including `venv/` and `tmp_model/`, to a
machine with the same OS and Python version. On the offline machine, install Ollama and copy its models
folder (`~/.ollama/models`, or `%USERPROFILE%\.ollama\models` on Windows).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Chat says *Could not reach Ollama* | Start Ollama (the desktop app, or `ollama serve`) |
| Chat says *Ollama does not have model …* | `ollama pull <model>` or set `OLLAMA_MODEL` to a model you have |
| `run.ps1` cannot be loaded / execution policy error | Run it as shown: `powershell -ExecutionPolicy Bypass -File .\run.ps1` |
| `Embedding model missing` | Run `setup.ps1` / `make setup` (or `python download_model.py`) with internet |
| `pip` fails building numpy/chromadb | You are on an unsupported Python. Use 3.11 or 3.12 |
| `pip` errors like `No module named 'pip._internal…'` or `No such file or directory` on Windows | Path too long: move the project to a short folder like `C:\dk`, delete `venv\` and rerun setup |
| Port 8000 already in use | `.\run.ps1 -Port 8080` or `make run PORT=8080` |
| Want to start over | Stop the app, delete `chroma_db/` (and `documents/` for the uploaded files) |

---

## Project layout

```text
.
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── routes/
│   │   ├── api_chat_search.py  # /chat, /chat-stream, /search, /debug/memory
│   │   ├── api_file_ingest.py  # /upload, /remove, /ingest, /clear_db
│   │   └── ui_routes.py        # / (UI) and /documents
│   ├── static/                 # CSS + JS front end (marked.js bundled, no CDN)
│   └── templates/index.html
├── utility/
│   ├── model_loader.py         # Shared embedding model + spaCy pipeline (loaded once)
│   ├── db_manager.py           # ChromaDB wrapper
│   ├── embedding_and_storing.py# Parse → chunk → embed → store
│   ├── parsing.py              # PDF text extraction
│   └── chunking_algs/          # Chunking algorithms (+ experiments)
├── config.py                   # Paths and settings
├── download_model.py           # One-time embedding model download
├── setup.ps1 / run.ps1         # Windows setup and launch
├── makefile                    # Linux/macOS setup and launch
└── requirements.txt
```

Runtime data (git-ignored): `venv/`, `tmp_model/`, `chroma_db/`, `documents/`, `pdfs/`.

---

## Changes in R1

These are relative to upstream `6729cb1`:

- **Fixed `/chat`**: it called Ollama without `"stream": false`, so parsing the reply always failed.
- **Fixed broken chunkers**: `graph-pagerank` (used by `/ingest`) and `dynamic` crashed with a
  `TypeError`. `/ingest` also tried to write a list as text.
- **One shared embedding model**: chunkers used to load a different model on every call
  (`all-MiniLM-L12-v2` / `all-mpnet-base-v2`), which needed internet and failed offline. Everything now
  uses the model in `tmp_model/`, and the spaCy pipeline is loaded once.
- **Dependencies**: added the missing `requests`, `networkx` and `en_core_web_sm`, and dropped the
  unused `nltk`.
- **Cross-platform setup**: new `setup.ps1` / `run.ps1` for Windows, a simplified Makefile and
  `download_model.py`.
- **Safer uploads**: filenames are sanitized (no path traversal), only `.pdf` / `.txt` are accepted, and
  re-uploading a file replaces it instead of duplicating it. `/ingest` only embeds newly converted PDFs.
- **Clearer errors** when Ollama is down or the model isn't pulled. Requests now have timeouts.
- **Front end**: chat listeners no longer stack up on every message, document on/off toggles now affect
  chat context, and `marked.js` loads correctly.

---

Released under the MIT license. Original project by [sage-bomb](https://github.com/sage-bomb/Deployable-Knowledge).
