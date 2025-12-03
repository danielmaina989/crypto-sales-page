from django.http import JsonResponse
from payments.models import Payment


def payment_status(request, checkout_id):
    payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
    if not payment:
        return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)

    return JsonResponse({
        'success': True,
        'status': payment.status,
        'receipt': payment.mpesa_receipt_number,
        'error': payment.error_message,
    })

