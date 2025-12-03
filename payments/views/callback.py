from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from payments.models import Payment
import json
from payments.utils.errors import MPESA_ERRORS
from payments.utils.notifications import notify_payment_success


@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    checkout_id = data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")
    result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode")
    result_desc = data.get("Body", {}).get("stkCallback", {}).get("ResultDesc")

    payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
    if not payment:
        return JsonResponse({"success": False, "message": "Payment not found"}, status=404)

    payment.callback_raw_data = data
    if result_code == 0:
        payment.status = "success"
        # Attempt to extract mpesa receipt number safely
        try:
            items = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
            # Try to find Receipt (may vary by MPESA)
            for it in items:
                if it.get('Name', '').lower() in ('mpesa_receipt_number','receiptnumber','transactionreceipt','mpesareceiptnumber'):
                    payment.mpesa_receipt_number = it.get('Value')
                    break
            else:
                # fallback: second item as previously used
                payment.mpesa_receipt_number = items[1].get('Value') if len(items) > 1 else None
        except Exception:
            payment.mpesa_receipt_number = None
        payment.error_code = None
        payment.error_message = None
    else:
        payment.status = "failed"
        payment.error_code = str(result_code)
        payment.error_message = MPESA_ERRORS.get(str(result_code), result_desc)

    payment.updated_at = timezone.now()
    payment.save()

    # Send notification for success (best-effort)
    if payment.status == 'success':
        try:
            notify_payment_success(payment, via=('email',))
        except Exception:
            pass

    return JsonResponse({"success": True})
