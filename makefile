# Makefile for Deployable-Knowledge (Linux / macOS). On Windows use setup.ps1 / run.ps1.

# === Offline-friendly environment for running ===
export CHROMA_TELEMETRY_ENABLED=false
export ANONYMIZED_TELEMETRY=False

# === Config (override with: make VAR=...) ===
VENV_NAME ?= venv
PYTHON    ?= python3
PY        := $(VENV_NAME)/bin/python
APP_MODULE?= app.main:app
PORT      ?= 8000
MODEL_FILE:= tmp_model/config.json

.PHONY: setup venv install model run dev clean

# ---------- ONE-TIME SETUP (needs internet) ----------
setup: venv install model
	@echo "Setup complete. Install Ollama, run 'ollama pull mistral:7b', then 'make run'."

venv:
	@test -x $(PY) || $(PYTHON) -m venv $(VENV_NAME)
	$(PY) -m pip install --upgrade pip

install: venv
	$(PY) -m pip install -r requirements.txt

model:
	$(PY) download_model.py

# ---------- RUN (works offline after setup) ----------
run:
	@test -x $(PY) || (echo "No venv. Run 'make setup' first."; exit 1)
	@test -f $(MODEL_FILE) || (echo "Embedding model missing. Run 'make setup' (needs internet once)."; exit 1)
	TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
	$(PY) -m uvicorn $(APP_MODULE) --host 127.0.0.1 --port $(PORT)

dev:
	TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
	$(PY) -m uvicorn $(APP_MODULE) --host 127.0.0.1 --port $(PORT) --reload

# ---------- housekeeping ----------
clean:
	rm -rf $(VENV_NAME) chroma_db/
