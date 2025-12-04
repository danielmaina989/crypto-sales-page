from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from payments.models import Payment
import json
from payments.utils.errors import MPESA_ERRORS
from payments.utils.notifications import notify_payment_success
import logging

logger = logging.getLogger(__name__)


def _safe_truncate(s, n=1000):
    try:
        return (s[:n] + '...') if isinstance(s, str) and len(s) > n else s
    except Exception:
        return 'unprintable'


@csrf_exempt
def mpesa_callback(request):
    """Handle MPESA callback/webhook.

    This endpoint accepts JSON or form-encoded bodies. It is resilient to slight
    variations in the incoming payload and logs a safe, truncated version for debugging.

    Important: to avoid repeated retries from the MPESA sandbox/relay, this view
    always returns HTTP 200 after attempting to process the callback. If a matching
    Payment is found, it will be updated; if not, we log and still return 200 so the
    caller does not repeatedly resend the callback.
    """
    raw_body = None
    data = None

    # --- Enhanced diagnostic logging: log host, full path, headers, and forwarding info ---
    try:
        host = request.get_host()
    except Exception:
        host = request.META.get('HTTP_HOST') or request.META.get('SERVER_NAME')

    full_path = request.get_full_path() if hasattr(request, 'get_full_path') else request.path
    remote_addr = request.META.get('REMOTE_ADDR')
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    proto = request.META.get('HTTP_X_FORWARDED_PROTO') or request.scheme

    try:
        hdrs = dict(request.headers) if hasattr(request, 'headers') else {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
        hdrs_json = json.dumps(hdrs)
    except Exception:
        hdrs_json = None

    logger.info('mpesa_callback incoming request: host=%s full_path=%s remote=%s xff=%s proto=%s', host, full_path, remote_addr, xff, proto)
    if hdrs_json:
        logger.debug('mpesa_callback headers: %s', _safe_truncate(hdrs_json, 1000))

    try:
        raw_body = request.body.decode('utf-8') if request.body else ''
    except Exception:
        raw_body = ''

    # Try JSON body first
    if raw_body:
        try:
            data = json.loads(raw_body)
        except Exception:
            # Try to be tolerant: sometimes services send form-encoded data with a JSON string in a field
            try:
                # Django populates request.POST for form-encoded bodies
                if hasattr(request, 'POST') and request.POST:
                    # if there's a key like 'Body' that contains JSON, try to parse it
                    if 'Body' in request.POST:
                        try:
                            data = json.loads(request.POST['Body'])
                        except Exception:
                            # sometimes nested under 'stkCallback' etc.
                            try:
                                # attempt to parse first value
                                first = next(iter(request.POST.values()), None)
                                if first:
                                    data = json.loads(first)
                            except Exception:
                                data = None
                    else:
                        # try to parse any first value as JSON
                        first = next(iter(request.POST.values()), None)
                        if first:
                            try:
                                data = json.loads(first)
                            except Exception:
                                data = None
                else:
                    data = None
            except Exception:
                data = None

    # Last-ditch: if still no data but request.POST dict has nested JSON-like structure, try to coerce
    if data is None and hasattr(request, 'POST') and request.POST:
        try:
            # Build a dict from POST items (non-JSON fallback)
            data = {k: request.POST.get(k) for k in request.POST.keys()}
        except Exception:
            data = None

    logger.info('mpesa_callback received: content_type=%s remote=%s body=%s',
                request.META.get('CONTENT_TYPE'), request.META.get('REMOTE_ADDR'), _safe_truncate(raw_body, 800))

    if not data:
        # Log and return 200 so MPESA/sandbox stops retrying. We don't have a payload to process.
        logger.warning('mpesa_callback: no parseable payload received (truncated body): %s', _safe_truncate(raw_body, 800))
        return JsonResponse({'success': True})

    # Extract standard fields safely
    try:
        body = data.get('Body') if isinstance(data, dict) else None
        stk = body.get('stkCallback') if isinstance(body, dict) else None
        checkout_id = None
        result_code = None
        result_desc = None
        if isinstance(stk, dict):
            checkout_id = stk.get('CheckoutRequestID')
            result_code = stk.get('ResultCode')
            result_desc = stk.get('ResultDesc')
        else:
            # Some payloads may include the stkCallback at the top level
            checkout_id = data.get('CheckoutRequestID') or data.get('checkout_request_id')
            result_code = data.get('ResultCode')
            result_desc = data.get('ResultDesc')
    except Exception as exc:
        logger.exception('mpesa_callback: error extracting callback fields: %s', exc)
        return JsonResponse({'success': True})

    payment = None
    try:
        if checkout_id:
            payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
    except Exception:
        payment = None

    if not payment:
        logger.warning('mpesa_callback: payment not found for checkout_id=%s', checkout_id)
        # Still return 200 to acknowledge receipt and avoid retries
        return JsonResponse({'success': True})

    # Persist the raw callback for auditing
    try:
        payment.callback_raw_data = data
    except Exception:
        # best effort
        payment.callback_raw_data = None

    try:
        if result_code == 0:
            payment.status = 'success'
            # Extract receipt safely
            try:
                items = stk.get('CallbackMetadata', {}).get('Item') if isinstance(stk, dict) else None
                if isinstance(items, list):
                    for it in items:
                        name = (it.get('Name') or '').lower()
                        if name in ('mpesa_receipt_number', 'receiptnumber', 'transactionreceipt', 'mpesareceiptnumber'):
                            payment.mpesa_receipt_number = it.get('Value')
                            break
                    else:
                        payment.mpesa_receipt_number = items[1].get('Value') if len(items) > 1 and isinstance(items[1], dict) else None
                else:
                    payment.mpesa_receipt_number = None
            except Exception:
                payment.mpesa_receipt_number = None
            payment.error_code = None
            payment.error_message = None
        else:
            payment.status = 'failed'
            payment.error_code = str(result_code) if result_code is not None else None
            payment.error_message = MPESA_ERRORS.get(str(result_code), result_desc)

        payment.updated_at = timezone.now()
        payment.save()
    except Exception as exc:
        logger.exception('mpesa_callback: failed to update payment %s: %s', checkout_id, exc)
        # return 200 to avoid MPESA retries
        return JsonResponse({'success': True})

    # Send notification for success (best-effort)
    if payment.status == 'success':
        try:
            notify_payment_success(payment, via=('email',))
        except Exception:
            logger.exception('mpesa_callback: notify_payment_success failed for payment %s', payment.id)

    return JsonResponse({'success': True})
