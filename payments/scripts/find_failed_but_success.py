from payments.models import Payment
from django.utils import timezone
import json

matches = []
for p in Payment.objects.filter(status='failed').order_by('-created_at'):
    raw = p.callback_raw_data
    if not raw:
        continue
    s = json.dumps(raw) if not isinstance(raw, str) else raw
    # look for common success indicators
    if '"ResultCode": 0' in s or '"ResultCode": 0' in s or '"ResponseCode": "0"' in s or '"ResponseCode": 0' in s:
        matches.append((p.id, s[:300]))

print('found', len(matches), 'candidates')
for pid, snippet in matches[:50]:
    print(pid, snippet)

