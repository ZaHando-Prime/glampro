"""
RAG (Retrieval-Augmented Generation) pipeline for Glam Pro Beauty Assistant.

Manages two ChromaDB collections:
  - "products"  : beauty product catalogue, with sponsored-boost logic
  - "app_help"  : Glam Pro app FAQ / walkthrough items

Embeddings are produced by the multilingual sentence-transformers model
`paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions), enabling Arabic
and English queries to match documents in either language.

IMPORTANT – Source-of-truth contract:
  The JSON files in the ``data/`` directory are ALWAYS the source of truth.
  On every server startup, the entire ChromaDB store is wiped and rebuilt
  from those files so that edits to the JSON are immediately reflected
  without any manual cache invalidation.
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple

# Disable ChromaDB telemetry to prevent posthog errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_data")
EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"

# How many candidate results to pull from each collection
_PRODUCT_K: int = 6
_HELP_K: int = 3

# ---------------------------------------------------------------------------
# Similarity thresholds
# ---------------------------------------------------------------------------
# Embeddings are L2-normalized (unit vectors), so ChromaDB L2 distances are
# always in the range [0, 2]:
#   distance=0   → identical          → similarity = 1/(1+0)   = 1.00
#   distance=0.77→ cosine_sim ≈ 0.70  → similarity = 1/(1+0.77)≈ 0.56  (similar)
#   distance=1.26→ cosine_sim ≈ 0.20  → similarity = 1/(1+1.26)≈ 0.44  (unrelated)
#   distance=1.41→ cosine_sim = 0     → similarity = 1/(1+1.41)≈ 0.41  (orthogonal)
#
# Set thresholds between the "similar" and "unrelated" zones:
_PRODUCT_THRESHOLD: float = 0.45   # products need to be at least loosely relevant
_HELP_THRESHOLD:    float = 0.50   # help items must be semantically on-topic

# Sponsored products receive a score boost to surface them preferentially.
_SPONSORED_BOOST: float = 1.2

# ---------------------------------------------------------------------------
# Module-level singletons (initialised once at startup)
# ---------------------------------------------------------------------------
_chroma_client: Optional[chromadb.PersistentClient] = None
_embedding_model: Optional[SentenceTransformer] = None


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def _create_chroma_client() -> chromadb.PersistentClient:
    """Create (or recreate) the ChromaDB persistent client."""
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def init_rag() -> None:
    """
    Load the embedding model and open the ChromaDB persistent client.
    Called once on application startup.
    """
    global _chroma_client, _embedding_model

    logger.info("Loading multilingual embedding model: %s", EMBEDDING_MODEL_NAME)
    _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info("Embedding model loaded.")

    _chroma_client = _create_chroma_client()
    logger.info("ChromaDB client initialised at: %s", CHROMA_PATH)


def reset_chroma_store() -> None:
    """
    Completely wipe the on-disk ChromaDB store and reinitialise the client.

    Call this **before** seeding from JSON files to guarantee that any
    previously persisted data (from earlier runs) is discarded and the
    JSON files are the sole source of truth.
    """
    global _chroma_client

    logger.info("Resetting ChromaDB store at: %s", CHROMA_PATH)
    try:
        # Close / discard the current client before wiping the directory.
        _chroma_client = None
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
            logger.info("ChromaDB store deleted successfully.")
    except Exception as exc:
        logger.warning("Could not delete ChromaDB store (will attempt to continue): %s", exc)

    # Recreate a fresh client on the now-empty (or newly created) directory.
    _chroma_client = _create_chroma_client()
    logger.info("ChromaDB client reinitialised – store is now empty.")


def _get_client() -> chromadb.PersistentClient:
    if _chroma_client is None:
        raise RuntimeError("RAG not initialised. Call init_rag() first.")
    return _chroma_client


def _embed(texts: List[str]) -> List[List[float]]:
    """
    Generate L2-normalised embeddings for a list of texts.

    Normalisation is critical: without it, raw embedding vectors from
    paraphrase-multilingual-MiniLM-L12-v2 have varying magnitudes that push
    L2 distances into the range 10–30+, making similarity scores drop below
    any useful threshold and causing all RAG results to be filtered out.

    With unit-normalised vectors the L2 distance is always in [0, 2] and
    our similarity transform 1/(1+d) maps cleanly to the [0.33, 1.0] range.
    """
    if _embedding_model is None:
        raise RuntimeError("Embedding model not loaded. Call init_rag() first.")
    return _embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,   # ← unit vectors → L2 distance ∈ [0, 2]
    ).tolist()


# ---------------------------------------------------------------------------
# Indexing helpers
# ---------------------------------------------------------------------------

def _delete_collection_if_exists(name: str) -> None:
    client = _get_client()
    try:
        client.delete_collection(name)
        logger.info("Deleted existing ChromaDB collection: %s", name)
    except Exception:
        pass  # Collection did not exist – that is fine


def index_products(items: List[Dict[str, Any]]) -> int:
    """
    (Re-)index the products ChromaDB collection from a list of product dicts.
    Deletes the existing collection first for a clean rebuild.

    Returns the number of documents indexed.
    """
    _delete_collection_if_exists("products")
    collection = _get_client().get_or_create_collection("products")

    if not items:
        logger.info("No products to index.")
        return 0

    documents: List[str] = []
    embeddings: List[List[float]] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for item in items:
        # Concatenate description + benefits as the indexed text
        benefits_text = " ".join(item.get("benefits", []))
        doc_text = f"{item['description']} {benefits_text}".strip()
        documents.append(doc_text)

        metadatas.append({
            "id": item["id"],
            "name": item["name"],
            "brand": item.get("brand", ""),
            "category": item.get("category", ""),
            "description": item.get("description", ""),
            "benefits": ", ".join(item.get("benefits", [])),
            "usage": item.get("usage", ""),
            "sponsored": str(item.get("sponsored", False)),  # ChromaDB metadata must be str/int/float
            "price": float(item.get("price", 0)),
            "currency": item.get("currency", "USD"),
        })
        ids.append(item["id"])

    embeddings = _embed(documents)
    collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d products.", len(items))
    return len(items)


def index_help(items: List[Dict[str, Any]]) -> int:
    """
    (Re-)index the app_help ChromaDB collection from a list of help dicts.
    Returns the number of documents indexed.
    """
    _delete_collection_if_exists("app_help")
    collection = _get_client().get_or_create_collection("app_help")

    if not items:
        logger.info("No help items to index.")
        return 0

    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for item in items:
        keywords_text = " ".join(item.get("keywords", []))
        doc_text = f"{item['question']} {keywords_text}".strip()
        documents.append(doc_text)

        metadatas.append({
            "id": item["id"],
            "question": item["question"],
            "answer": item["answer"],
            "keywords": ", ".join(item.get("keywords", [])),
        })
        ids.append(item["id"])

    embeddings = _embed(documents)
    collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d help items.", len(items))
    return len(items)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _l2_to_similarity(distance: float) -> float:
    """
    Convert an L2 distance to a [0, 1] similarity score.
    Uses a simple 1 / (1 + d) transform so that distance=0 → 1.0.
    """
    return 1.0 / (1.0 + distance)


def retrieve(query: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Query both ChromaDB collections and return relevant context.

    Returns
    -------
    products : list of product metadata dicts, sorted by boosted similarity desc
    help_items : list of help metadata dicts
    """
    client = _get_client()
    query_embedding = _embed([query])[0]

    # --- Products ---
    retrieved_products: List[Dict[str, Any]] = []
    try:
        prod_collection = client.get_collection("products")
        prod_count = prod_collection.count()
        if prod_count > 0:
            k = min(_PRODUCT_K, prod_count)
            results = prod_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["metadatas", "distances"],
            )
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                similarity = _l2_to_similarity(dist)
                if similarity < _PRODUCT_THRESHOLD:
                    continue  # Below relevance threshold – skip
                # Apply sponsored boost
                is_sponsored = meta.get("sponsored", "False") == "True"
                boosted_score = similarity * (_SPONSORED_BOOST if is_sponsored else 1.0)
                retrieved_products.append({
                    **meta,
                    "sponsored": is_sponsored,  # convert back to bool for prompt builder
                    "_score": boosted_score,
                })
            # Sort by boosted score descending
            retrieved_products.sort(key=lambda x: x["_score"], reverse=True)
    except Exception as exc:
        logger.warning("Product retrieval failed or collection empty: %s", exc)

    # --- Help ---
    retrieved_help: List[Dict[str, Any]] = []
    try:
        help_collection = client.get_collection("app_help")
        help_count = help_collection.count()
        if help_count > 0:
            k = min(_HELP_K, help_count)
            results = help_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["metadatas", "distances"],
            )
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                similarity = _l2_to_similarity(dist)
                # Log every candidate so threshold issues are visible in logs
                logger.info(
                    "Help candidate score=%.4f (need>=%.2f) | %s",
                    similarity, _HELP_THRESHOLD, meta.get("question", "")[:60],
                )
                if similarity >= _HELP_THRESHOLD:
                    retrieved_help.append({**meta, "_score": similarity})
    except Exception as exc:
        logger.warning("Help retrieval failed or collection empty: %s", exc)

    return retrieved_products, retrieved_help


def collection_sizes() -> Dict[str, int]:
    """Return the number of documents in each collection (for health check)."""
    client = _get_client()
    sizes: Dict[str, int] = {"products": 0, "app_help": 0}
    for name in sizes:
        try:
            sizes[name] = client.get_collection(name).count()
        except Exception:
            pass
    return sizes
