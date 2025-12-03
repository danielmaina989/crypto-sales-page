# Placeholder for background tasks (e.g., Celery tasks)
from django.utils import timezone

from payments.utils.mpesa_api import query_transaction_status  # may raise if requests missing
from payments.models import Payment

# Try to import Celery task decorator if available
try:
    from core.celery import app as celery_app
    from celery import shared_task
except Exception:
    celery_app = None
    shared_task = None


def _poll_payment_status_sync(payment_id: int):
    """Synchronous fallback that queries MPESA for status and updates the Payment."""
    payment = Payment.objects.filter(pk=payment_id).first()
    if not payment:
        return None

    try:
        result = query_transaction_status(payment.checkout_request_id or payment.merchant_request_id)
    except Exception as exc:
        payment.error_message = str(exc)
        payment.updated_at = timezone.now()
        payment.save()
        return None

    # Example result parsing (depends on MPESA response shape)
    result_code = result.get('ResultCode') if isinstance(result, dict) else None
    if result_code == 0:
        payment.status = 'success'
        payment.mpesa_receipt_number = result.get('MpesaReceiptNumber') or result.get('ReceiptNumber')
    else:
        payment.status = 'failed'
        payment.error_code = str(result_code)
        payment.error_message = result.get('ResultDesc') if isinstance(result, dict) else str(result)

    payment.updated_at = timezone.now()
    payment.save()
    return payment


if shared_task is not None:
    @shared_task(bind=True)
    def poll_payment_status(self, payment_id: int):
        return _poll_payment_status_sync(payment_id)
else:
    def poll_payment_status(payment_id: int):
        return _poll_payment_status_sync(payment_id)
