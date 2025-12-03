import json
from decimal import Decimal, InvalidOperation
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from payments.utils.validators import validate_phone_number
from payments.utils.mpesa_api import initiate_stk_push
from payments.models import Payment


@method_decorator(csrf_exempt, name='dispatch')
@require_POST
def initiate_payment(request):
    # Allow authenticated users; for API tests we will use force_login
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=403)

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
    except Exception as exc:
        payment.status = 'failed'
        payment.error_message = str(exc)
        payment.save()
        return JsonResponse({'success': False, 'message': 'failed to initiate', 'error': str(exc)}, status=500)

    # map possible response keys safely
    checkout_id = resp.get('CheckoutRequestID') or resp.get('checkout_request_id')
    merchant_req_id = resp.get('MerchantRequestID') or resp.get('MerchantRequestID')

    if checkout_id:
        payment.checkout_request_id = checkout_id
    if merchant_req_id:
        payment.merchant_request_id = merchant_req_id
    payment.save()

    return JsonResponse({'success': True, 'checkout_request_id': checkout_id, 'raw_response': resp})

