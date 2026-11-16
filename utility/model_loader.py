"""Shared loaders so the embedding model and spaCy pipeline are loaded once.

Before this module existed, every chunking call created a brand-new
SentenceTransformer (and spaCy pipeline), often by a *different* model name
than the one used for storage. That was slow, needed internet access on
every upload, and failed outright in offline mode.
"""
from functools import lru_cache

from config import EMBEDDING_MODEL_NAME, LOCAL_MODEL_PATH


def _model_is_cached() -> bool:
    return (LOCAL_MODEL_PATH / "config.json").exists() or (LOCAL_MODEL_PATH / "modules.json").exists()


@lru_cache(maxsize=1)
def get_embedding_model():
    """Return the single shared SentenceTransformer instance.

    Loads from ``tmp_model/`` when present; otherwise downloads
    ``EMBEDDING_MODEL_NAME`` once and saves it there for offline use.
    """
    from sentence_transformers import SentenceTransformer

    if _model_is_cached():
        return SentenceTransformer(str(LOCAL_MODEL_PATH))

    print(f"Embedding model not found in {LOCAL_MODEL_PATH}; downloading {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    LOCAL_MODEL_PATH.mkdir(parents=True, exist_ok=True)
    model.save(str(LOCAL_MODEL_PATH))
    return model


def resolve_model(model=None):
    """Accept a model instance, a model name, or None and return a model.

    Model *names* are ignored on purpose: the app always uses the one shared
    model so embeddings from chunking and from storage/search match.
    """
    if model is not None and not isinstance(model, str):
        return model
    return get_embedding_model()


@lru_cache(maxsize=1)
def get_spacy_nlp():
    """Return the cached spaCy pipeline (en_core_web_sm + PyTextRank)."""
    import os
    # PyTextRank pulls in GitPython, which raises at import time when no `git`
    # executable is on PATH (typical on offline/field machines). The app never
    # uses git, so silence that check.
    os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
    import spacy
    import pytextrank  # noqa: F401  (registers the "textrank" pipe)

    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    nlp.add_pipe("textrank", last=True)
    return nlp
