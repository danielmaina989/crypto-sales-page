# Script to reconcile failed payments based on stored callback_raw_data
from payments.models import Payment
from django.utils import timezone
import json

fixed = []
checked = 0
for p in Payment.objects.filter(status='failed').order_by('-created_at'):
    checked += 1
    data = p.callback_raw_data
    if not data:
        continue
    try:
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        continue
    body = data.get('Body') if isinstance(data, dict) else None
    stk = body.get('stkCallback') if isinstance(body, dict) else None
    rc = None
    if isinstance(stk, dict):
        rc = stk.get('ResultCode')
    else:
        rc = data.get('ResponseCode') or data.get('ResultCode')
    try:
        if rc is not None and int(rc) == 0:
            # extract receipt
            receipt = None
            try:
                if isinstance(stk, dict):
                    items = stk.get('CallbackMetadata', {}).get('Item')
                    if isinstance(items, list):
                        for it in items:
                            name = (it.get('Name') or '').lower()
                            if 'receipt' in name or 'mpesa_receipt' in name:
                                receipt = it.get('Value')
                                break
                if not receipt:
                    receipt = data.get('MpesaReceiptNumber') or data.get('ReceiptNumber')
            except Exception:
                receipt = None

            p.status = 'success'
            if receipt:
                p.mpesa_receipt_number = receipt
            p.error_code = None
            p.error_message = None
            p.updated_at = timezone.now()
            p.save()
            fixed.append((p.id, receipt))
    except Exception:
        continue

print(f'Checked {checked} failed payments')
print(f'Fixed {len(fixed)} payments')
for pid, rcpt in fixed:
    print(f' - id={pid} receipt={rcpt}')

