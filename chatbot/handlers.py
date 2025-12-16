from .services import (
    lookup_payment_by_phone,
    lookup_payment_by_reference,
    format_payment_response,
    lookup_payment,
)


def handle_generic_status():
    return {
        "reply": (
            "I can help you check a payment status.\n\n"
            "Please share **one** of the following:\n"
            "• Phone number used\n"
            "• MPESA receipt number\n"
            "• Checkout request ID"
        ),
        "status": "need_identifier",
    }


def handle_payment_lookup(entities: dict):
    phone = entities.get('phone')
    receipt = entities.get('receipt') or entities.get('receipt')
    checkout = entities.get('checkout_request_id') or entities.get('checkout')

    result = lookup_payment(phone=phone, receipt=receipt, checkout=checkout)

    if result is None:
        return {
            "reply": "❌ I couldn’t find a payment with that information. Please double-check and try again.",
            "status": "not_found",
        }

    if result.get('multiple'):
        return {
            "reply": (
                f"⚠️ I found **{result['count']} payments** using that phone number.\n\n"
                "Please provide a **receipt number** or **checkout request ID** to narrow it down."
            ),
            "status": "multiple",
        }

    status_map = {
        "success": "✅ Payment successful",
        "pending": "⏳ Payment pending confirmation",
        "failed": "❌ Payment failed",
    }

    return {
        "reply": (
            f"{status_map.get(result['status'], 'ℹ️ Payment status')}\n\n"
            f"Amount: KES {result['amount']}\n"
            f"Receipt: {result['receipt'] or '-'}\n"
            f"Date: {result['created'].strftime('%b %d, %Y %H:%M')}"
        ),
        "status": result['status'],
    }


def handle_intent(intent_data: dict) -> dict:
    intent = intent_data.get('intent') if intent_data else None

    if intent == 'payment_lookup_phone' or intent == 'payment_lookup' or intent == 'payment_lookup_reference':
        return handle_payment_lookup(intent_data.get('entities', {}))

    if intent == 'payment_lookup_prompt' or intent == 'payment_status_generic':
        return handle_generic_status()

    return {
        'message': (
            "🤖 I didn’t quite understand that.\n\n"
            "You can ask:\n"
            "• Check payment\n"
            "• MPESA status\n"
            "• Send phone number"
        )
    }
