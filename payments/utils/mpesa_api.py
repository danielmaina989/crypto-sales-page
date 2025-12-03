import base64
from datetime import datetime
from django.conf import settings

try:
    import requests
except Exception:  # requests may not be installed in this environment
    requests = None


def _base_url():
    return "https://api.safaricom.co.ke" if getattr(settings, 'MPESA_ENV', 'sandbox') == "production" else "https://sandbox.safaricom.co.ke"


def get_access_token():
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    key = settings.MPESA_CONSUMER_KEY
    secret = settings.MPESA_CONSUMER_SECRET
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, headers={"Authorization": f"Basic {auth}"}, timeout=15)
    try:
        resp.raise_for_status()
    except Exception:
        pass  # Allow fallback to occur
    return resp.json().get("access_token")


def _stk_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def initiate_stk_push(phone_number, amount, account_ref, description):
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    access_token = get_access_token()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    shortcode = settings.MPESA_SHORTCODE
    password = _stk_password(shortcode, settings.MPESA_PASSKEY, timestamp)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_ref,
        "TransactionDesc": description,
    }

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def query_transaction_status(identifier):
    """Query transaction status by CheckoutRequestID or MerchantRequestID.

    Returns the MPESA API JSON response or raises RuntimeError if requests missing.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    access_token = get_access_token()
    shortcode = settings.MPESA_SHORTCODE
    payload = {
        "BusinessShortCode": shortcode,
        "Identifier": identifier,
    }

    url = f"{_base_url()}/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()
