from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from payments.models import Payment


@csrf_exempt
def simulate_callback(request, checkout_id):
    """Dev-only endpoint to simulate an MPESA callback for a payment.

    This will mark the matching Payment as `success` and set a fake receipt number.
    Enabled only when DEBUG=True or MPESA_SIMULATE is set in environment/settings.
    """
    simulate_enabled = getattr(settings, 'DEBUG', False) or getattr(settings, 'MPESA_SIMULATE', False)
    if not simulate_enabled:
        return JsonResponse({'success': False, 'message': 'simulate_callback endpoint is disabled'}, status=403)

    payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
    if not payment:
        return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)

    # Create a simple simulated callback payload for audit
    payload = {
        'Body': {
            'stkCallback': {
                'CheckoutRequestID': checkout_id,
                'ResultCode': 0,
                'ResultDesc': 'The service request is processed successfully.',
                'CallbackMetadata': {
                    'Item': [
                        {'Name': 'MpesaReceiptNumber', 'Value': f'SIMREC{timezone.now().strftime("%Y%m%d%H%M%S")}'},
                    ]
                }
            }
        }
    }

    # Update payment model similarly to real callback
    try:
        payment.callback_raw_data = payload
        payment.status = 'success'
        # extract the simulated receipt
        try:
            items = payload['Body']['stkCallback']['CallbackMetadata']['Item']
            payment.mpesa_receipt_number = items[0].get('Value')
        except Exception:
            payment.mpesa_receipt_number = None
        payment.error_code = None
        payment.error_message = None
        payment.updated_at = timezone.now()
        payment.save()
    except Exception as exc:
        return JsonResponse({'success': False, 'message': 'Failed to update payment', 'error': str(exc)}, status=500)

    return JsonResponse({'success': True, 'message': 'Simulated callback applied', 'receipt': payment.mpesa_receipt_number})
