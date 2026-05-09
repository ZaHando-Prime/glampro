"""
Pydantic data models for Glam Pro Beauty Assistant API.
Covers request/response validation and JSON data schemas for products and help items.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# JSON data schemas (used by admin upload endpoints)
# ---------------------------------------------------------------------------

class ProductItem(BaseModel):
    """A single product entry in products.json."""
    id: str = Field(..., description="Unique product identifier, e.g. 'prod-001'")
    name: str = Field(..., description="Product display name")
    brand: str = Field(..., description="Brand name")
    category: str = Field(..., description="Category, e.g. 'skincare', 'makeup'")
    description: str = Field(..., description="Detailed product description")
    benefits: List[str] = Field(default_factory=list, description="List of key benefits")
    usage: str = Field(default="", description="How to use the product")
    sponsored: bool = Field(default=False, description="Whether this is a sponsored product")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD", description="Price currency code")


class HelpItem(BaseModel):
    """A single help / FAQ entry in app_help.json."""
    id: str = Field(..., description="Unique help entry identifier, e.g. 'help-001'")
    question: str = Field(..., description="The user-facing question")
    answer: str = Field(..., description="Full step-by-step answer")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Payload sent by the Flutter app on each user turn."""
    session_id: str = Field(..., description="Session UUID obtained from /session/new")
    message: str = Field(..., min_length=1, description="The user's latest message")


class ChatResponse(BaseModel):
    """Returned by POST /chat."""
    reply: str = Field(..., description="The assistant's text reply")
    session_id: str = Field(..., description="Echo of the session ID for convenience")


class SessionResponse(BaseModel):
    """Returned by GET /session/new."""
    session_id: str = Field(..., description="Newly created UUID session identifier")


class HealthResponse(BaseModel):
    """Returned by GET /health."""
    status: str = Field(default="ok")
    llm_loaded: bool
    products_count: int
    help_count: int


class AdminUploadResponse(BaseModel):
    """Returned after a successful admin JSON upload and re-index."""
    message: str
    indexed_count: int
