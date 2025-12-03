from django.contrib.auth import get_user_model
import json
from decimal import Decimal, InvalidOperation
import logging
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from payments.utils.validators import validate_phone_number
from payments.utils.mpesa_api import initiate_stk_push, get_access_token
import os
from payments.models import Payment
from payments.utils import mpesa_api as _mpesa_api
from payments.tasks import poll_payment_status

# Import requests exceptions if available
try:
    import requests
    from requests.exceptions import RequestException as _RequestException
except Exception:
    requests = None
    _RequestException = Exception

# Import tenacity RetryError if tenacity is installed
try:
    from tenacity import RetryError as _RetryError
except Exception:
    class _RetryError(Exception):
        pass

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def initiate_payment(request):
    try:
        # Allow authenticated users; if unauthenticated create/assign a fallback guest user
        User = get_user_model()
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            # Use or create a dedicated guest/system user for payments
            user, _created = User.objects.get_or_create(username='payments_guest', defaults={'email': ''})
            # attempt to ensure unusable password (silent safe)
            try:
                if not user.has_usable_password():
                    user.set_unusable_password()
                    user.save()
            except Exception:
                pass

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

        amount = payload.get('amount')
        phone = payload.get('phone_number')
        account_ref = payload.get('account_ref', '')
        description = payload.get('description', '')

        if not amount or not phone:
            return JsonResponse({'success': False, 'message': 'amount and phone_number are required'}, status=400)

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return JsonResponse({'success': False, 'message': 'invalid amount'}, status=400)

        if not validate_phone_number(phone):
            return JsonResponse({'success': False, 'message': 'invalid phone_number'}, status=400)

        # Pre-flight: ensure we can call the MPESA API (requests package) or that simulation is enabled
        try:
            requests_available = getattr(_mpesa_api, 'requests', None) is not None
            simulate = _mpesa_api._simulate_enabled()
        except Exception:
            requests_available = False
            simulate = False

        if not requests_available and not simulate:
            return JsonResponse({
                'success': False,
                'message': "MPESA integration requires the 'requests' package or enable simulation.",
                'hint': "Install via: pip install requests or enable simulation: export MPESA_SIMULATE=1"
            }, status=500)

        # If not simulating, ensure required MPESA configuration exists to avoid obscure 500s later
        if not simulate:
            required = [
                'MPESA_CONSUMER_KEY',
                'MPESA_CONSUMER_SECRET',
                'MPESA_SHORTCODE',
                'MPESA_PASSKEY',
                'MPESA_CALLBACK_URL',
            ]
            missing = [k for k in required if not hasattr(settings, k)]
            if missing:
                return JsonResponse({
                    'success': False,
                    'message': 'Missing MPESA configuration',
                    'missing': missing,
                    'hint': 'Set the missing settings as environment variables or enable simulation (MPESA_SIMULATE=1)'
                }, status=500)

        payment = Payment.objects.create(
            user=user,
            amount=amount,
            phone_number=phone,
            account_ref=account_ref,
            description=description,
            status='pending',
        )

        try:
            resp = initiate_stk_push(phone, amount, account_ref, description)
        except (_RetryError, _RequestException) as exc:
            # Upstream/network error while calling MPESA
            payment.status = 'failed'
            payment.error_message = str(exc)
            payment.save()
            logger.exception('MPESA upstream request failed')
            return JsonResponse({
                'success': False,
                'message': 'Upstream MPESA request failed',
                'error': str(exc)
            }, status=502)
        except Exception as exc:
            payment.status = 'failed'
            payment.error_message = str(exc)
            payment.save()
            logger.exception('Failed to initiate STK push')
            return JsonResponse({'success': False, 'message': 'failed to initiate', 'error': str(exc)}, status=500)

        # map possible response keys safely
        checkout_id = None
        if isinstance(resp, dict):
            checkout_id = resp.get('CheckoutRequestID') or resp.get('checkout_request_id') or resp.get('CheckoutRequestId')
            merchant_req_id = resp.get('MerchantRequestID') or resp.get('MerchantRequestId') or resp.get('merchant_request_id')
        else:
            merchant_req_id = None

        if checkout_id:
            payment.checkout_request_id = checkout_id
        if merchant_req_id:
            payment.merchant_request_id = merchant_req_id

        # Ensure raw_response is serializable
        raw = resp
        try:
            json.dumps(raw)
        except Exception:
            raw = repr(resp)

        payment.callback_raw_data = raw if isinstance(raw, (dict, list, type(None))) else None
        payment.save()

        # If we are running in simulation mode, mark the payment as successful immediately
        try:
            if simulate:
                # Create a simulated callback-like record and update payment
                sim_receipt = f"SIMREC{timezone.now().strftime('%Y%m%d%H%M%S')}"
                try:
                    # attach a small callback payload for audit
                    payment.callback_raw_data = {
                        'Body': {
                            'stkCallback': {
                                'CheckoutRequestID': checkout_id,
                                'ResultCode': 0,
                                'ResultDesc': 'Simulation - processed successfully',
                                'CallbackMetadata': {'Item': [{'Name': 'MpesaReceiptNumber', 'Value': sim_receipt}]}
                            }
                        }
                    }
                except Exception:
                    payment.callback_raw_data = payment.callback_raw_data
                payment.status = 'success'
                payment.mpesa_receipt_number = sim_receipt
                payment.error_code = None
                payment.error_message = None
                payment.updated_at = timezone.now()
                payment.save()
        except Exception:
            # If simulation post-processing fails, do not prevent returning the normal response
            logger.exception('Failed to apply simulated success for payment')

        # For non-simulated flows, verify we can fetch an access token before enqueuing background polls.
        if not simulate:
            try:
                # This will raise RuntimeError on HTTP error; we catch and handle below
                get_access_token()
            except Exception as exc:
                # Check for 403-like responses in the error message and treat as dev-only condition
                err_text = str(exc).lower()
                logger.error('Access token fetch failed before enqueuing poll for payment %s: %s', payment.id, err_text)
                # If running in DEBUG or explicit env var, fall back to simulation (dev-only)
                force_sim = getattr(settings, 'DEBUG', False) or os.getenv('MPESA_FORCE_SIMULATE_IF_TOKEN_FAIL') in ('1', 'true', 'True')
                if force_sim:
                    try:
                        sim_receipt = f"SIMREC{timezone.now().strftime('%Y%m%d%H%M%S')}"
                        payment.callback_raw_data = {
                            'Body': {
                                'stkCallback': {
                                    'CheckoutRequestID': checkout_id,
                                    'ResultCode': 0,
                                    'ResultDesc': 'Simulation fallback - processed successfully',
                                    'CallbackMetadata': {'Item': [{'Name': 'MpesaReceiptNumber', 'Value': sim_receipt}]}
                                }
                            }
                        }
                        payment.status = 'success'
                        payment.mpesa_receipt_number = sim_receipt
                        payment.error_code = None
                        payment.error_message = f"Autofallback to simulation due to token error: {err_text}"[:1000]
                        payment.updated_at = timezone.now()
                        payment.save()
                        logger.info('Applied dev fallback simulation for payment %s after token failure', payment.id)
                    except Exception:
                        logger.exception('Failed to apply dev fallback simulation for payment %s', payment.id)
                else:
                    payment.status = 'failed'
                    payment.error_message = f"Failed to fetch MPESA access token: {err_text}"
                    payment.updated_at = timezone.now()
                    payment.save()
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to fetch MPESA access token',
                        'error': err_text,
                        'hint': 'If you are developing locally, set MPESA_SIMULATE=1 or MPESA_FORCE_SIMULATE_IF_TOKEN_FAIL=1 to bypass sandbox calls.'
                    }, status=502)

        # If not simulating, enqueue background polling via Celery (if available) so status updates are fetched
        try:
            if not simulate:
                try:
                    # schedule a background task to poll status; initial attempt starts after 3 seconds
                    if hasattr(poll_payment_status, 'delay'):
                        # Respect global MPESA polling delay from settings
                        configured_delay = int(getattr(settings, 'MPESA_POLL_DELAY_SECONDS', 12))
                        poll_payment_status.delay(payment.id, attempts=0, max_attempts=40, delay=configured_delay)
                    else:
                        # Fallback to synchronous polling if Celery not configured
                        poll_payment_status(payment.id)
                except Exception:
                    logger.exception('Failed to enqueue poll_payment_status task; will rely on webhook/callbacks')
        except Exception:
            logger.exception('Unexpected error when trying to queue poll task')

        return JsonResponse({'success': True, 'checkout_request_id': checkout_id, 'raw_response': raw})

    except Exception as exc:
        # Catch-all to avoid a hard 500; log and return JSON
        logger.exception('Unhandled error in initiate_payment')
        try:
            # mark payment failed if created earlier in this request
            payment
        except NameError:
            payment = None
        if payment:
            try:
                payment.status = 'failed'
                payment.error_message = str(exc)
                payment.save()
            except Exception:
                logger.exception('Failed to persist payment failure')
        return JsonResponse({'success': False, 'message': 'internal server error', 'error': str(exc)}, status=500)
