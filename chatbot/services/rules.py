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

