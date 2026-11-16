"""Download the embedding model into tmp_model/ so the app can run offline.

Run once while you have internet access:

    python download_model.py
"""
from utility.model_loader import get_embedding_model
from config import LOCAL_MODEL_PATH

if __name__ == "__main__":
    model = get_embedding_model()
    print(f"Embedding model ready in {LOCAL_MODEL_PATH} "
          f"(dimension {model.get_sentence_embedding_dimension()}).")
