from django.core.management.base import BaseCommand
from payments.models import Payment
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reconcile failed payments using stored callback_raw_data and update statuses where callback shows success.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of payments to process (0 = all)')

    def handle(self, *args, **options):
        dry = options['dry_run']
        limit = options['limit']

        qs = Payment.objects.filter(status='failed').order_by('-created_at')
        total = qs.count()
        self.stdout.write(f'Found {total} failed payments to inspect')

        if limit and limit > 0:
            qs = qs[:limit]

        fixed = []
        for p in qs:
            data = p.callback_raw_data
            if not data:
                continue
            try:
                # Normalize to dict if JSON string
                if isinstance(data, str):
                    data = json.loads(data)
            except Exception:
                # skip unparsable
                continue

            # Look for common success indicators
            success = False
            receipt = None

            # Case 1: MPESA new style Body->stkCallback with ResultCode
            try:
                body = data.get('Body') if isinstance(data, dict) else None
                stk = body.get('stkCallback') if isinstance(body, dict) else None
                if isinstance(stk, dict):
                    rc = stk.get('ResultCode')
                    # coerce and check
                    if rc is not None:
                        try:
                            if int(rc) == 0:
                                success = True
                                # extract receipt metadata
                                items = stk.get('CallbackMetadata', {}).get('Item')
                                if isinstance(items, list):
                                    for it in items:
                                        name = (it.get('Name') or '').lower()
                                        if 'receipt' in name or 'mpesa_receipt' in name:
                                            receipt = it.get('Value')
                                            break
                        except Exception:
                            # unable to coerce rc to int; ignore
                            pass
                # Case 2: older style top-level ResponseCode / ResponseDescription
                if not success and isinstance(data, dict):
                    resp_code = data.get('ResponseCode') or data.get('responseCode')
                    if resp_code is not None and str(resp_code).strip() == '0':
                        success = True
                        receipt = receipt or data.get('MpesaReceiptNumber') or data.get('ReceiptNumber')
            except Exception:
                logger.exception('Error while parsing callback for payment %s', p.id)

            if success:
                fixed.append((p.id, receipt))
                if not dry:
                    p.status = 'success'
                    if receipt:
                        p.mpesa_receipt_number = receipt
                    p.error_code = None
                    p.error_message = None
                    p.updated_at = timezone.now()
                    p.save()

        self.stdout.write(f'Processed {qs.count()} payments; marked {len(fixed)} as success')
        if fixed:
            self.stdout.write('Updated payments:')
            for pid, rec in fixed:
                self.stdout.write(f' - id={pid} receipt={rec}')
        else:
            self.stdout.write('No payments needed updating')
