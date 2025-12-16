from datetime import timedelta
from django.utils import timezone
import logging

from payments.models import Payment

logger = logging.getLogger(__name__)

LOOKUP_WINDOW_HOURS = 24


def lookup_payment_by_phone(phone: str):
    since = timezone.now() - timedelta(hours=LOOKUP_WINDOW_HOURS)
    try:
        payment = (
            Payment.objects
            .filter(phone_number=phone, created_at__gte=since)
            .order_by('-created_at')
            .first()
        )
        logger.info('Chat lookup by phone=%s found=%s', phone, bool(payment))
        return payment
    except Exception as exc:
        logger.exception('Error looking up payment by phone: %s', exc)
        return None


def lookup_payment_by_reference(reference: str):
    try:
        payment = Payment.objects.filter(
            checkout_request_id__iexact=reference
        ).first()
        logger.info('Chat lookup by reference=%s found=%s', reference, bool(payment))
        return payment
    except Exception as exc:
        logger.exception('Error looking up payment by reference: %s', exc)
        return None


def format_payment_response(payment: Payment | None) -> dict:
    if not payment:
        return {"message": "❌ No recent payment found. Please confirm the phone number or try again."}

    # normalize status strings to user-friendly text
    status_map = {
        'success': '✅ Successful',
        'pending': '⏳ Pending',
        'failed': '❌ Failed',
        # fallback uppercase variants
        'SUCCESS': '✅ Successful',
        'PENDING': '⏳ Pending',
        'FAILED': '❌ Failed',
    }

    status_label = status_map.get(payment.status, str(payment.status))

    msg = (
        f"{status_label}\n\n"
        f"Amount: KES {payment.amount}\n"
        f"Phone: {payment.phone_number}\n"
        f"Reference: {payment.checkout_request_id or payment.merchant_request_id or '-'}\n"
        f"Date: {payment.created_at.strftime('%d %b %Y %H:%M')}"
    )

    return {"message": msg, "status": payment.status}


# New function: unified lookup returning structured info

def lookup_payment(phone=None, receipt=None, checkout=None):
    qs = Payment.objects.all()

    if checkout:
        qs = qs.filter(checkout_request_id__iexact=checkout)
    elif receipt:
        qs = qs.filter(mpesa_receipt_number__iexact=receipt)
    elif phone:
        # match last 9 digits for flexibility
        p = phone.strip()
        qs = qs.filter(phone_number__icontains=p[-9:])
    else:
        return None

    count = qs.count()
    if count == 0:
        return None

    if count > 1:
        return {"multiple": True, "count": count}

    p = qs.first()
    return {
        "id": p.id,
        "status": p.status,
        "amount": p.amount,
        "receipt": p.mpesa_receipt_number,
        "created": p.created_at,
    }
