from django.http import JsonResponse
from payments.models import Payment


def payment_status(request, checkout_id):
    # Accept either a numeric payment ID or a CheckoutRequestID/merchant_request_id
    payment = None
    try:
        # numeric id -> primary key lookup
        if str(checkout_id).isdigit():
            payment = Payment.objects.filter(pk=int(checkout_id)).first()
        if not payment:
            # try matching known request id fields
            payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
        if not payment:
            payment = Payment.objects.filter(merchant_request_id=checkout_id).first()
    except Exception:
        payment = None

    if not payment:
        return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)

    # Normalize status for frontend polling (uppercase expected values)
    raw_status = (payment.status or '').lower()
    if raw_status in ('success', 'succeeded', 'completed'):
        status = 'SUCCESS'
    elif raw_status in ('failed', 'error'):
        status = 'FAILED'
    else:
        status = 'PENDING'

    return JsonResponse({
        'success': True,
        'status': status,
        'receipt': payment.mpesa_receipt_number,
        'error': payment.error_message,
        'payment_id': payment.id,
        'checkout_request_id': payment.checkout_request_id,
    })
