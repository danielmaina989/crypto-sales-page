import base64
from datetime import datetime
from django.conf import settings
import os

try:
    import requests
except Exception:  # requests may not be installed in this environment
    requests = None

from .retry import retry


def _base_url():
    return "https://api.safaricom.co.ke" if getattr(settings, 'MPESA_ENV', 'sandbox') == "production" else "https://sandbox.safaricom.co.ke"


def _simulate_enabled():
    # Allow enabling simulation via Django settings or environment variable
    return getattr(settings, 'MPESA_SIMULATE', False) or os.getenv('MPESA_SIMULATE') in ('1', 'true', 'True')


@retry(max_attempts=3, base_delay=0.5)
def _http_get(url, headers=None, timeout=15):
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


@retry(max_attempts=3, base_delay=0.5)
def _http_post(url, json=None, headers=None, timeout=20):
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")
    resp = requests.post(url, json=json, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


def get_access_token():
    # If simulation is enabled, return a dummy token to allow offline testing
    if _simulate_enabled():
        return 'SIMULATED_TOKEN'

    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    key = settings.MPESA_CONSUMER_KEY
    secret = settings.MPESA_CONSUMER_SECRET
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    resp = _http_get(url, headers={"Authorization": f"Basic {auth}"})
    return resp.json().get("access_token")


def _stk_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def initiate_stk_push(phone_number, amount, account_ref, description):
    # Development simulation: if enabled, return a fake successful response
    if _simulate_enabled():
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        fake_checkout = f"SIMCHK{ts}"
        fake_merchant = f"SIMMR{ts}"
        return {
            "ResponseCode": "0",
            "ResponseDescription": "Simulation - STK initiated",
            "CheckoutRequestID": fake_checkout,
            "MerchantRequestID": fake_merchant,
        }

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
    resp = _http_post(url, json=payload, headers=headers)
    return resp.json()


def query_transaction_status(identifier):
    """Query transaction status by CheckoutRequestID or MerchantRequestID.

    Returns the MPESA API JSON response or raises RuntimeError if requests missing.
    """
    # Support simulation for query too
    if _simulate_enabled():
        # Simulate that pending transactions transition to success after a short time
        return {"ResultCode": 0, "ResultDesc": "The service request is processed successfully.", "MpesaReceiptNumber": f"SIMREC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"}

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
    resp = _http_post(url, json=payload, headers=headers)
    return resp.json()
