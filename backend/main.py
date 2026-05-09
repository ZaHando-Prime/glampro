"""
Glam Pro Beauty Assistant – FastAPI application entry point.

Startup sequence:
  1. Load LLM (non-blocking if model file missing)
  2. Init RAG (embedding model + ChromaDB client)
  3. Reset ChromaDB store (wipe stale data so JSON files are always the source of truth)
  4. Seed ChromaDB from local JSON files (products.json + app_help.json)

This means that ANY change you make to the JSON files in the ``data/``
directory will be reflected the next time the server starts – no manual
cache invalidation is required.

Endpoints:
  GET  /health
  GET  /session/new
  POST /chat
  POST /admin/upload/products   (protected by X-API-Key header)
  POST /admin/upload/help       (protected by X-API-Key header)
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

import llm as llm_module
import memory
import prompt as prompt_module
import rag as rag_module
from models import (
    AdminUploadResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    HelpItem,
    ProductItem,
    SessionResponse,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "change-me-in-production")
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))
PRODUCTS_JSON: Path = DATA_DIR / "products.json"
HELP_JSON: Path = DATA_DIR / "app_help.json"


# ---------------------------------------------------------------------------
# Lifespan – runs on startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("=== Glam Pro Beauty Assistant – Starting up ===")

    # 1. Load LLM
    llm_module.init_llm()

    # 2. Init RAG (embedding model + ChromaDB)
    rag_module.init_rag()

    # 3. Wipe the ChromaDB store so JSON edits are always picked up on restart.
    #    The JSON files in data/ are the single source of truth; ChromaDB is
    #    just a runtime vector cache that is rebuilt from scratch every time.
    logger.info("Resetting ChromaDB store to pick up any JSON file changes...")
    rag_module.reset_chroma_store()

    # 4. Seed from local JSON files (best-effort; missing files are skipped)
    _seed_from_local_files()

    logger.info("=== Startup complete ===")
    yield
    # --- Shutdown (nothing to do for now) ---
    logger.info("=== Glam Pro Beauty Assistant – Shutting down ===")


def _seed_from_local_files() -> None:
    """
    Load products.json and app_help.json from the data/ directory and index
    them into the freshly reset ChromaDB store.

    This always runs on startup (after reset_chroma_store), so any edits
    you make to the JSON files take effect the moment the server restarts.
    """
    if PRODUCTS_JSON.is_file():
        try:
            items = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
            validated = [ProductItem(**i).model_dump() for i in items]
            count = rag_module.index_products(validated)
            logger.info("Seeded %d products from %s", count, PRODUCTS_JSON)
        except Exception as exc:
            logger.error("Failed to seed products from file: %s", exc)
    else:
        logger.info("No local products.json found – starting with empty products collection.")

    if HELP_JSON.is_file():
        try:
            items = json.loads(HELP_JSON.read_text(encoding="utf-8"))
            validated = [HelpItem(**i).model_dump() for i in items]
            count = rag_module.index_help(validated)
            logger.info("Seeded %d help items from %s", count, HELP_JSON)
        except Exception as exc:
            logger.error("Failed to seed help from file: %s", exc)
    else:
        logger.info("No local app_help.json found – starting with empty help collection.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Glam Pro Beauty Assistant API",
    description=(
        "Local-LLM powered beauty chatbot with RAG for products and app help. "
        "Supports Arabic and English."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins so the Flutter app can connect from any device/emulator.
# In production, restrict this to your domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Admin key dependency
# ---------------------------------------------------------------------------

def verify_admin_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """FastAPI dependency that validates the admin API key."""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns LLM status and the number of documents indexed in each RAG collection.
    """
    sizes = rag_module.collection_sizes()
    return HealthResponse(
        status="ok",
        llm_loaded=llm_module.is_loaded(),
        products_count=sizes["products"],
        help_count=sizes["app_help"],
    )


@app.get("/session/new", response_model=SessionResponse, tags=["Chat"])
async def new_session() -> SessionResponse:
    """Create a new conversation session and return its UUID."""
    session_id = memory.create_session()
    logger.info("New session created: %s", session_id)
    return SessionResponse(session_id=session_id)


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Flow
    ----
    1. Validate / create the session.
    2. Run RAG retrieval against both ChromaDB collections.
    3. DEBUG – log every retrieved help item and its similarity score so you
       can verify the retrieval is working.
    4a. DIRECT-ANSWER MODE (help item found):
        Return the exact answer from app_help.json WITHOUT calling the LLM.
        Small models (≤7B) cannot reliably follow "use these exact steps"
        instructions, so bypassing the LLM is the only 100 % reliable approach.
    4b. LLM MODE (no help item found):
        Call the local Llama model for general beauty / product questions.
    5. Store the exchange in session memory and return the reply.
    """
    # Ensure session is valid
    memory.get_or_create_session(request.session_id)

    # ------------------------------------------------------------------ #
    # RAG Retrieval
    # ------------------------------------------------------------------ #
    products, help_items = rag_module.retrieve(request.message)

    # Debug: log every retrieved help item and its score so you can see
    # whether the correct item is being found.
    if help_items:
        logger.info(
            "Session %s | RAG found %d help item(s):",
            request.session_id[:8], len(help_items),
        )
        for idx, h in enumerate(help_items):
            logger.info(
                "  [%d] score=%.4f  Q: %s",
                idx, h.get("_score", 0), h.get("question", "")[:80],
            )
    else:
        logger.warning(
            "Session %s | RAG returned NO help items for query: %s",
            request.session_id[:8], request.message[:80],
        )

    # ------------------------------------------------------------------ #
    # 4a. DIRECT-ANSWER MODE – bypass LLM when a help item is found
    # ------------------------------------------------------------------ #
    if help_items:
        reply = help_items[0]["answer"]
        memory.add_exchange(request.session_id, request.message, reply)
        logger.info(
            "Session %s | DIRECT ANSWER returned (no LLM). Score=%.4f | Q: %s",
            request.session_id[:8],
            help_items[0].get("_score", 0),
            help_items[0].get("question", "")[:60],
        )
        return ChatResponse(reply=reply, session_id=request.session_id)

    # ------------------------------------------------------------------ #
    # 4b. LLM MODE – general beauty / product question, no help match
    # ------------------------------------------------------------------ #
    if not llm_module.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The AI model is not loaded. Please set the MODEL_PATH environment "
                "variable to a valid GGUF model file and restart the server."
            ),
        )

    history = memory.get_history(request.session_id)
    full_prompt, _ = prompt_module.build_prompt(
        user_message=request.message,
        products=products,
        help_items=[],          # already handled above; pass empty here
        history=history,
    )

    reply = llm_module.generate(full_prompt)
    if reply is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model inference failed. Please check the server logs.",
        )

    memory.add_exchange(request.session_id, request.message, reply)
    logger.info(
        "Session %s | LLM reply | User: %s | Reply: %d chars",
        request.session_id[:8], request.message[:60], len(reply),
    )
    return ChatResponse(reply=reply, session_id=request.session_id)


@app.post(
    "/admin/upload/products",
    response_model=AdminUploadResponse,
    tags=["Admin"],
    dependencies=[Depends(verify_admin_key)],
)
async def upload_products(file: UploadFile = File(...)) -> AdminUploadResponse:
    """
    Admin endpoint: upload a new products.json and re-index the products collection.

    The file must be a JSON array of product objects matching the ProductItem schema.
    The existing collection is deleted and rebuilt from the uploaded data.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a .json file.",
        )

    raw = await file.read()
    try:
        items_raw: List[dict] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON: {exc}",
        ) from exc

    # Validate each item against the Pydantic schema
    validated: List[dict] = []
    errors: List[str] = []
    for idx, item in enumerate(items_raw):
        try:
            validated.append(ProductItem(**item).model_dump())
        except Exception as exc:
            errors.append(f"Item {idx}: {exc}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": errors},
        )

    count = rag_module.index_products(validated)

    # Persist the uploaded file so it survives a restart
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PRODUCTS_JSON.write_bytes(raw)

    logger.info("Admin re-indexed %d products.", count)
    return AdminUploadResponse(message="Products collection rebuilt successfully.", indexed_count=count)


@app.post(
    "/admin/upload/help",
    response_model=AdminUploadResponse,
    tags=["Admin"],
    dependencies=[Depends(verify_admin_key)],
)
async def upload_help(file: UploadFile = File(...)) -> AdminUploadResponse:
    """
    Admin endpoint: upload a new app_help.json and re-index the help collection.

    The file must be a JSON array of help objects matching the HelpItem schema.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a .json file.",
        )

    raw = await file.read()
    try:
        items_raw: List[dict] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON: {exc}",
        ) from exc

    validated: List[dict] = []
    errors: List[str] = []
    for idx, item in enumerate(items_raw):
        try:
            validated.append(HelpItem(**item).model_dump())
        except Exception as exc:
            errors.append(f"Item {idx}: {exc}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": errors},
        )

    count = rag_module.index_help(validated)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HELP_JSON.write_bytes(raw)

    logger.info("Admin re-indexed %d help items.", count)
    return AdminUploadResponse(message="Help collection rebuilt successfully.", indexed_count=count)
