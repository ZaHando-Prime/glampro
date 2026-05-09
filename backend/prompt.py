"""
Prompt template builder for Glam Pro Beauty Assistant.

The LLM is ONLY called for general beauty / product questions.
App navigation questions are answered directly from app_help.json in main.py
(bypassing the LLM entirely), so this prompt has NO app-navigation framing.

Two-mode architecture
---------------------
  App help question  →  main.py returns JSON answer directly  (no LLM)
  Beauty question    →  build_prompt() → LLM generates beauty advice + products
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# System prompt  –  pure beauty advisor, zero app-navigation framing
# ---------------------------------------------------------------------------
# The LLM never sees app navigation context here because those questions are
# already handled by the direct-answer path.  Removing that framing prevents
# the model from hallucinating fake "Open Glam Pro → Tap X" steps.
_SYSTEM_PROMPT = """\
You are Glam Pro Beauty Assistant, a knowledgeable and warm beauty expert.

Your job is to give practical beauty advice and naturally recommend relevant \
products from the context below.

Rules:
1. Always reply in the SAME language as the user's message (Arabic or English).
2. Give concrete, helpful beauty advice based on the user's question.
3. If one or two products from the context are relevant, mention them naturally \
   in your advice (name + one key benefit). Do NOT list prices unless asked. \
   Do NOT sound like an advertisement.
4. NEVER mention or invent app navigation steps (e.g. "open the app", \
   "tap here", "go to settings"). That is handled elsewhere.
5. Keep your reply warm, concise, and under 120 words.\
"""

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
# NOTE: <|begin_of_text|> is injected automatically by llama-cpp-python.
# Including it here causes a duplicate-token RuntimeWarning, so we omit it.
_PROMPT_TEMPLATE = """\
<|start_header_id|>system<|end_header_id|>

{system_prompt}

CONTEXT:
- Current date: {current_date}
{product_section}\
{history_section}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

_PRODUCT_SECTION_TEMPLATE = """\
- Relevant products you may recommend (★ = sponsored / featured):
{product_lines}

"""

_HISTORY_SECTION_TEMPLATE = """\
- Conversation history (most recent last):
{history_lines}

"""


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _format_product(p: Dict[str, Any]) -> str:
    """Convert a retrieved product dict into a single bullet-point line."""
    star = "★ " if p.get("sponsored") else ""
    benefits = ", ".join(p.get("benefits", [])) or "N/A"
    price = f"${p.get('price', 0):.2f} {p.get('currency', 'USD')}"
    return (
        f"  • {star}{p['name']} ({p.get('brand', '')}) – "
        f"{p.get('description', '')} "
        f"[Benefits: {benefits}] [Price: {price}]"
    )


def _format_history(history: List[Dict[str, str]]) -> str:
    """Format message history as a readable dialogue."""
    lines = []
    for msg in history:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"  {role_label}: {msg['content']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_answer_prefill(help_items: Optional[List[Dict[str, Any]]]) -> str:
    """
    Return the exact answer text from the top-ranked help item.
    Returns '' if no help items were retrieved.
    (Kept for compatibility – currently unused since direct-answer mode in
    main.py returns before ever calling build_prompt when help items exist.)
    """
    if not help_items:
        return ""
    return help_items[0].get("answer", "")


def build_prompt(
    user_message: str,
    products: Optional[List[Dict[str, Any]]] = None,
    help_items: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    current_date: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Build the LLM prompt for general beauty / product questions.

    This is only called when no app-help item was retrieved (those are handled
    by the direct-answer path in main.py).  ``help_items`` is accepted for
    API compatibility but is intentionally ignored here.

    Parameters
    ----------
    user_message:   The latest user message (raw text).
    products:       List of retrieved product dicts (sorted by boosted score).
    help_items:     Ignored – kept for backward-compatible call signature.
    history:        Conversation history from memory.get_history().
    current_date:   ISO date string; defaults to today.

    Returns
    -------
    (prompt, "")
        prompt  – full prompt string ready for llm.generate()
        ""      – empty prefill (no prefilling needed for beauty questions)
    """
    today = current_date or str(date.today())

    # --- product section ---
    if products:
        product_lines = "\n".join(_format_product(p) for p in products)
        product_section = _PRODUCT_SECTION_TEMPLATE.format(product_lines=product_lines)
    else:
        product_section = ""

    # --- history section ---
    if history:
        history_lines = _format_history(history)
        history_section = _HISTORY_SECTION_TEMPLATE.format(history_lines=history_lines)
    else:
        history_section = ""

    prompt = _PROMPT_TEMPLATE.format(
        system_prompt=_SYSTEM_PROMPT,
        current_date=today,
        product_section=product_section,
        history_section=history_section,
        user_message=user_message,
    )

    return prompt, ""
