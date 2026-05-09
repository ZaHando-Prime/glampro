"""
LLM wrapper for Glam Pro Beauty Assistant.

Loads a quantised Llama 3.2-3B Instruct GGUF model using llama-cpp-python
and exposes a single `generate()` function.

The model path is read from the MODEL_PATH environment variable.  If the
file is missing the module degrades gracefully: `is_loaded()` returns False
and `generate()` returns None, allowing the API to return a friendly error.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf"))
N_CTX: int = int(os.getenv("LLM_N_CTX", "4096"))
N_THREADS: int = int(os.getenv("LLM_N_THREADS", "8"))
MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "512"))
# Low temperature = less hallucination; the model sticks to the retrieved context.
# Range: 0.0 (fully deterministic) – 1.0 (highly creative). 0.1 is ideal for RAG.
TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_llm = None  # type: ignore[var-annotated]


def init_llm() -> bool:
    """
    Attempt to load the GGUF model.  Returns True on success, False on failure.
    Called once at application startup.
    """
    global _llm

    if not os.path.isfile(MODEL_PATH):
        logger.warning(
            "LLM model file not found at '%s'. "
            "The /chat endpoint will return a service-unavailable error until "
            "a model is provided. Set MODEL_PATH env var to the correct path.",
            MODEL_PATH,
        )
        return False

    try:
        from llama_cpp import Llama  # type: ignore[import]

        logger.info("Loading LLM from: %s (n_ctx=%d, threads=%d)", MODEL_PATH, N_CTX, N_THREADS)
        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            verbose=False,
        )
        logger.info("LLM loaded successfully.")
        return True
    except Exception as exc:
        logger.error("Failed to load LLM: %s", exc, exc_info=True)
        return False


def is_loaded() -> bool:
    """Return True if the LLM is ready to handle requests."""
    return _llm is not None


def generate(prompt: str) -> Optional[str]:
    """
    Run inference with the loaded Llama model.

    Parameters
    ----------
    prompt : str
        The fully assembled instruction prompt (built by prompt.py).

    Returns
    -------
    str | None
        The generated text, or None if the model is not loaded / inference fails.
    """
    if _llm is None:
        logger.error("generate() called but LLM is not loaded.")
        return None

    try:
        output = _llm(
            prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            stop=["<|eot_id|>", "<|end_of_text|>"],
            echo=False,
        )
        # llama-cpp-python returns a dict with 'choices'
        text: str = output["choices"][0]["text"].strip()
        return text
    except Exception as exc:
        logger.error("LLM inference failed: %s", exc, exc_info=True)
        return None
