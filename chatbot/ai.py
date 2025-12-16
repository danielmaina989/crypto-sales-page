# Minimal AI fallback stub for intent detection.
# This module is a placeholder. It returns a safe 'unknown' intent when no AI
# provider is configured. When you add OpenAI or other LLMs, replace the
# implementation of `ai_detect_intent` to call the provider and return
# a dict like {"intent": "payment_lookup_phone", "phone": "071..."}.

import json
import logging

logger = logging.getLogger(__name__)


def ai_detect_intent(message: str) -> dict:
    """AI fallback that returns a safe structured dict. Currently returns unknown.

    Replace this function with calls to an LLM provider that returns JSON.
    Ensure the provider returns only structured JSON (intent + entities).
    """
    logger.info('AI fallback invoked for message: %s', message[:120])
    # Conservative default
    return {"intent": "unknown"}

