import re

# Patterns
PHONE_REGEX = re.compile(r"(?:\+?254|0)?7\d{8}")
CHECKOUT_REGEX = re.compile(r"\bws_CO_\w+\b", re.IGNORECASE)
RECEIPT_REGEX = re.compile(r"\b[A-Z]{2,10}[0-9]{5,}\b")

PHONE_RE = re.compile(r"(07\d{8}|2547\d{8})")
WS_CO_RE = re.compile(r"(ws_co_[A-Za-z0-9_\-]+)", re.IGNORECASE)


# Keep the small helper for the widget's simple replies
def handle_message(text: str) -> str | None:
    if not text:
        return "Please type a question."
    t = text.lower()
    # basic rules
    if 'mpesa' in t or 'm-pesa' in t:
        return "You can pay using MPESA from the Buy button. If you need help, open the payment modal and follow the prompts."
    if 'bitcoin' in t or 'btc' in t:
        return "Bitcoin (BTC) is available — go to Market or click Buy on the homepage."
    if 'wallet' in t:
        return "Each crypto card has a wallet address and a QR code you can copy."
    if 'price' in t or 'rate' in t:
        return "Prices are shown live on the Market page; click a coin to see current USD/KES prices."
    if 'help' in t:
        return "Ask about payments, wallet addresses, or where to find receipts."
    return None


def detect_intent(message: str) -> dict:
    """Detect intents and entities using deterministic rules.

    Returns a dict with keys: intent, confidence, entities
    """
    text = (message or "").strip()
    if not text:
        return {"intent": "unknown", "confidence": "low", "entities": {}}

    lower = text.lower()

    phone_m = PHONE_REGEX.search(text)
    checkout_m = CHECKOUT_REGEX.search(text)
    receipt_m = RECEIPT_REGEX.search(text)

    if phone_m or checkout_m or receipt_m:
        return {
            "intent": "payment_lookup",
            "confidence": "high",
            "entities": {
                "phone": phone_m.group() if phone_m else None,
                "checkout_request_id": checkout_m.group() if checkout_m else None,
                "receipt": receipt_m.group() if receipt_m else None,
            },
        }

    # generic status keywords
    for k in ("payment", "paid", "status", "mpesa", "transaction"):
        if k in lower:
            return {"intent": "payment_status_generic", "confidence": "low", "entities": {}}

    return {"intent": "unknown", "confidence": "low", "entities": {}}

