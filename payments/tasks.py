# Placeholder for background tasks (e.g., Celery tasks)
from django.utils import timezone
import logging
from django.conf import settings

from payments.utils.mpesa_api import query_transaction_status  # may raise if requests missing
from payments.models import Payment

# Try to import Celery task decorator if available
try:
    from core.celery import app as celery_app
    from celery import shared_task
except Exception:
    celery_app = None
    shared_task = None

logger = logging.getLogger(__name__)


def _poll_payment_status_sync(payment_id: int):
    """Synchronous fallback that queries MPESA for status and updates the Payment."""
    payment = Payment.objects.filter(pk=payment_id).first()
    if not payment:
        logger.debug('sync_poll: payment not found: %s', payment_id)
        return None

    try:
        result = query_transaction_status(payment.checkout_request_id or payment.merchant_request_id)
    except Exception as exc:
        logger.exception('sync_poll: error querying transaction status for payment %s: %s', payment_id, exc)
        payment.error_message = str(exc)
        payment.updated_at = timezone.now()
        payment.save()
        return None

    if not isinstance(result, dict):
        logger.warning('sync_poll: unexpected query result type for payment %s: %s', payment_id, type(result))
        payment.error_message = f'Unexpected query result: {result}'
        payment.updated_at = timezone.now()
        payment.save()
        return None

    # Example result parsing (depends on MPESA response shape)
    result_code = result.get('ResultCode')
    if result_code == 0:
        payment.status = 'success'
        payment.mpesa_receipt_number = result.get('MpesaReceiptNumber') or result.get('ReceiptNumber')
    else:
        payment.status = 'failed'
        payment.error_code = str(result_code)
        payment.error_message = result.get('ResultDesc')

    payment.updated_at = timezone.now()
    payment.save()
    return payment


if shared_task is not None:
    @shared_task(bind=True, max_retries=None)
    def poll_payment_status(self, payment_id: int, attempts: int = 0, max_attempts: int = 40, delay: int = 12):
        """Celery task that polls MPESA transaction status, retrying with a countdown until success or max attempts.

        Behaviour improvements:
        - Read configurable defaults from Django settings (MPESA_POLL_MAX_ATTEMPTS, MPESA_POLL_DELAY_SECONDS)
        - Include Celery task id in logs (self.request.id)
        - Treat non-dict/None results as transient and retry
        - Use rate-limited delays (default 12s) to respect M-Pesa's 5 requests/60s limit
        """
        task_id = getattr(getattr(self, 'request', None), 'id', None)
        # Allow settings to override defaults
        # Default delay is 12s: with max_attempts=40, worst case is 480s (8 minutes) with ~40 requests over that window
        # This keeps us under M-Pesa's 5 req/60s limit when spread across 12s intervals
        configured_max = int(getattr(settings, 'MPESA_POLL_MAX_ATTEMPTS', max_attempts))
        configured_delay = int(getattr(settings, 'MPESA_POLL_DELAY_SECONDS', delay))
        current_attempt = attempts + 1

        logger.info('poll_payment_status: task=%s starting attempt %s/%s for payment_id=%s', task_id, current_attempt, configured_max, payment_id)

        payment = Payment.objects.filter(pk=payment_id).first()
        if not payment:
            logger.warning('poll_payment_status: task=%s payment not found: %s', task_id, payment_id)
            return None

        try:
            result = query_transaction_status(payment.checkout_request_id or payment.merchant_request_id)
            logger.debug('poll_payment_status: task=%s query result for payment_id=%s attempt=%s: %s', task_id, payment_id, current_attempt, result)
        except Exception as exc:
            logger.exception('poll_payment_status: task=%s error querying transaction status for payment %s (attempt %s/%s): %s', task_id, payment_id, current_attempt, configured_max, str(exc))
            # retry if we haven't exhausted attempts
            if attempts < configured_max:
                logger.info('poll_payment_status: task=%s scheduling retry %s for payment_id=%s in %s seconds', task_id, current_attempt + 1, payment_id, configured_delay)
                raise self.retry(exc=exc, countdown=configured_delay, kwargs={
                    'attempts': attempts + 1,
                    'max_attempts': configured_max,
                    'delay': configured_delay,
                })
            # mark as pending after exhausting retries due to transient errors so callback can still update
            payment.status = 'pending'
            payment.error_message = f'Exhausted polling retries due to upstream error: {str(exc)[:500]}'
            payment.updated_at = timezone.now()
            payment.save()
            logger.error('poll_payment_status: task=%s exhausted retries for payment_id=%s due to errors; left as pending for webhook', task_id, payment_id)
            return None

        # Defensive handling if result is None or not a dict
        if not isinstance(result, dict):
            logger.warning('poll_payment_status: task=%s unexpected query result type for payment %s on attempt %s: %s', task_id, payment_id, current_attempt, type(result))
            if attempts < configured_max:
                logger.info('poll_payment_status: task=%s scheduling retry %s for payment_id=%s in %s seconds (due to unexpected result)', task_id, current_attempt + 1, payment_id, configured_delay)
                raise self.retry(countdown=configured_delay, kwargs={
                    'attempts': attempts + 1,
                    'max_attempts': configured_max,
                    'delay': configured_delay,
                })
            else:
                # Keep payment as pending when result is unexpected, allow webhook/callback to determine final state
                payment.status = 'pending'
                payment.error_message = f'Unexpected query result after retries: {result}'
                payment.updated_at = timezone.now()
                payment.save()
                logger.error('poll_payment_status: task=%s exhausted attempts for payment_id=%s; unexpected result retained as pending', task_id, payment_id)
                return payment

        # parse result
        result_code_raw = result.get('ResultCode')
        try:
            result_code = int(result_code_raw) if result_code_raw is not None else None
        except Exception:
            logger.warning('poll_payment_status: task=%s could not coerce ResultCode to int for payment %s: %r', task_id, payment_id, result_code_raw)
            result_code = None
        if result_code == 0:
            receipt = result.get('MpesaReceiptNumber') or result.get('ReceiptNumber')
            payment.status = 'success'
            payment.mpesa_receipt_number = receipt
            payment.error_code = None
            payment.error_message = None
            payment.updated_at = timezone.now()
            payment.save()
            logger.info('poll_payment_status: task=%s payment %s succeeded on attempt %s; receipt=%s', task_id, payment_id, current_attempt, receipt)
            return payment

        # not successful yet
        logger.info('poll_payment_status: task=%s payment_id=%s not successful on attempt %s (ResultCode=%s)', task_id, payment_id, current_attempt, result_code)
        if attempts < configured_max:
            # schedule another check
            logger.info('poll_payment_status: task=%s scheduling retry %s for payment_id=%s in %s seconds', task_id, current_attempt + 1, payment_id, configured_delay)
            raise self.retry(countdown=configured_delay, kwargs={
                'attempts': attempts + 1,
                'max_attempts': configured_max,
                'delay': configured_delay,
            })

        # exhausted attempts -> mark failed with details from response
        # Only mark as failed here because we have a definitive response (non-zero ResultCode) after retries
        payment.status = 'failed'
        payment.error_code = str(result_code) if result_code is not None else str(result_code_raw)
        payment.error_message = result.get('ResultDesc') if isinstance(result, dict) else str(result)
        payment.updated_at = timezone.now()
        payment.save()
        logger.error('poll_payment_status: task=%s exhausted attempts for payment_id=%s; final ResultCode=%s; error=%s', task_id, payment_id, result_code, payment.error_message)
        return payment

else:
    def poll_payment_status(payment_id: int):
        return _poll_payment_status_sync(payment_id)

    # Compatibility alias: older code or external callers may expect `poll_stk_status` task name.
    # Re-export the same task so either name works. When Celery is enabled, both refer to the
    # same shared task implementation defined above.
    try:
        # If the shared task exists, make an alias usable by delay()/apply_async()
        if shared_task is not None:
            poll_stk_status = poll_payment_status
    except Exception:
        poll_stk_status = poll_payment_status
