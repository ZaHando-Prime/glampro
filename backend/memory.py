"""
In-memory session conversation store for Glam Pro Beauty Assistant.

Each session keeps the last 6 user-assistant exchanges (12 messages total).
Uses a deque with maxlen to automatically drop oldest messages when the limit
is exceeded, preventing context-window overflow.
"""

from __future__ import annotations

import uuid
from collections import deque
from typing import Dict, List

# -----------------------------------------------------------------------
# Type alias: each message is {"role": "user"|"assistant", "content": str}
# -----------------------------------------------------------------------
Message = Dict[str, str]

# Maximum number of individual messages stored per session (6 exchanges × 2)
_MAX_MESSAGES: int = 12

# Global session store: session_id → deque of Message dicts
_sessions: Dict[str, deque] = {}


def create_session() -> str:
    """Create a new session and return its UUID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = deque(maxlen=_MAX_MESSAGES)
    return session_id


def get_or_create_session(session_id: str) -> str:
    """
    Ensure a session exists for the given ID.
    If the ID is unknown (e.g. app restart), create it transparently.
    Returns the (potentially unchanged) session_id.
    """
    if session_id not in _sessions:
        _sessions[session_id] = deque(maxlen=_MAX_MESSAGES)
    return session_id


def add_exchange(session_id: str, user_message: str, assistant_reply: str) -> None:
    """
    Append a complete user-assistant exchange to the session history.
    The deque automatically evicts the oldest messages once the maxlen is reached.
    """
    session = _sessions.get(session_id)
    if session is None:
        _sessions[session_id] = deque(maxlen=_MAX_MESSAGES)
        session = _sessions[session_id]
    session.append({"role": "user", "content": user_message})
    session.append({"role": "assistant", "content": assistant_reply})


def get_history(session_id: str) -> List[Message]:
    """Return the current message history for a session as a plain list."""
    session = _sessions.get(session_id)
    if session is None:
        return []
    return list(session)


def clear_session(session_id: str) -> None:
    """Remove all history for a session (useful for testing)."""
    if session_id in _sessions:
        _sessions[session_id].clear()


def session_count() -> int:
    """Return total number of active sessions (for monitoring)."""
    return len(_sessions)
