import base64
from datetime import datetime
from django.conf import settings
import os
import logging
import json
import time
import threading

try:
    import requests
    from requests.exceptions import HTTPError as _HTTPError
    from requests.exceptions import ConnectionError as _ConnectionError, Timeout as _Timeout
except Exception:  # requests may not be installed in this environment
    requests = None
    _HTTPError = Exception
    _ConnectionError = Exception
    _Timeout = Exception

from .retry import retry
from .rate_limit import wait_for_rate_limit

logger = logging.getLogger(__name__)


class MPesaAuthError(RuntimeError):
    """Raised when MPESA OAuth/token fetch fails due to HTTP issues (e.g., WAF/403)."""
    pass


# Define which exceptions should be considered 'network' and retriable
_retry_network_exceptions = ( _ConnectionError, _Timeout ) if requests is not None else (Exception,)


def _redact_headers(headers):
    """Return a shallow copy of headers with Authorization redacted for safe logging."""
    if not headers:
        return headers
    try:
        # headers may be a dict-like
        red = {}
        for k, v in (headers.items() if hasattr(headers, 'items') else headers):
            if k and k.lower() == 'authorization':
                red[k] = 'REDACTED'
            else:
                red[k] = v
        return red
    except Exception:
        # fallback: don't attempt to stringify large headers
        return 'REDACTED_HEADERS'


def _base_url():
    return "https://api.safaricom.co.ke" if getattr(settings, 'MPESA_ENV', 'sandbox') == "production" else "https://sandbox.safaricom.co.ke"


def _simulate_enabled():
    # Allow enabling simulation via Django settings or environment variable
    return getattr(settings, 'MPESA_SIMULATE', False) or os.getenv('MPESA_SIMULATE') in ('1', 'true', 'True')


def _redact_sensitive(d: dict) -> dict:
    """Return a shallow copy of d with common sensitive keys redacted (access_token, password, passkey).
    Keeps the structure shallow to avoid accidental large copies.
    """
    if not isinstance(d, dict):
        return d
    redacted = {}
    sensitive_keys = {'access_token', 'password', 'passkey', 'MPESA_CONSUMER_SECRET', 'mpesa_passkey'}
    for k, v in d.items():
        if k and any(sk.lower() in k.lower() for sk in sensitive_keys):
            redacted[k] = 'REDACTED'
        else:
            redacted[k] = v
    return redacted


@retry(max_attempts=3, base_delay=0.5, exceptions=_retry_network_exceptions)
def _http_get(url, headers=None, timeout=15):
    """HTTP GET with sane default headers to reduce Incapsula/WAF blocks.

    - Adds a browser-like User-Agent and Accept headers
    - Optionally sets Origin from MPESA_CALLBACK_URL when available
    - Retries only on network-level exceptions (ConnectionError/Timeout)
    - Raises RuntimeError on non-network HTTP status errors (403/4xx/5xx)
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    # Default safe headers to mimic a real browser request
    safe_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    # If a callback URL is configured, provide an Origin header derived from it
    try:
        callback = getattr(settings, 'MPESA_CALLBACK_URL', '')
        if callback:
            from urllib.parse import urlparse
            p = urlparse(callback)
            if p.scheme and p.netloc:
                origin = f"{p.scheme}://{p.netloc}"
                safe_headers.setdefault('Origin', origin)
    except Exception:
        # don't fail if parsing origin fails
        pass

    # Merge with caller headers (caller headers take precedence)
    if headers:
        safe_headers.update(headers)

    try:
        resp = requests.get(url, headers=safe_headers, timeout=timeout)
    except Exception as e:
        logger.exception("HTTP GET to %s failed (network/error): %s", url, str(e))
        raise

    # If the sandbox returns 403 with Incapsula HTML, surface a clear error
    if resp.status_code == 403:
        body = None
        try:
            body = resp.text
        except Exception:
            body = ''
        lower = (body or '').lower()
        safe_h = _redact_headers(safe_headers)
        if 'incapsula' in lower or 'access denied' in lower or 'blocked' in lower:
            logger.error("MPESA HTTP GET blocked by WAF/Incapsula: url=%s status=%s headers=%s", url, resp.status_code, safe_h)
            raise RuntimeError(f"HTTP GET {url} returned 403: blocked by WAF/Incapsula")
        # Generic 403
        logger.error("MPESA HTTP GET returned 403: url=%s headers=%s body=%s", url, safe_h, (body or '')[:500])
        raise RuntimeError(f"HTTP GET {url} returned 403: {body[:500] if body else 'no body'}")

    try:
        resp.raise_for_status()
    except _HTTPError as e:
        body = None
        try:
            body = resp.text
        except Exception:
            body = str(e)
        short_body = (body[:1000] + '...') if body and len(body) > 1000 else body
        safe_h = _redact_headers(safe_headers)
        logger.error("MPESA HTTP GET error: url=%s status=%s body=%s headers=%s", url, resp.status_code, short_body, safe_h)
        # Non-network HTTP errors are considered unretriable here (return fast)
        raise RuntimeError(f"HTTP GET {url} returned {resp.status_code}: {short_body}") from e

    return resp


def _http_post(url, payload=None, headers=None, timeout=20):
    """Send a JSON POST. `payload` is used to avoid shadowing the json module.
    
    Rate-limit errors (429) are NOT retried here—instead, they bubble up to the caller
    (poll_payment_status) which can apply backoff at the task level.
    Network errors are retried with exponential backoff.
    
    Rate limiting is applied BEFORE the request to respect M-Pesa sandbox limits.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")
    
    # Apply rate limiting before making the request
    logger.debug("_http_post: waiting for rate limit slot before POST to %s", url)
    wait_for_rate_limit()
    logger.debug("_http_post: rate limit slot acquired, proceeding with POST to %s", url)
    
    # Helper for retrying network-level errors (not 429 rate limits)
    @retry(max_attempts=3, base_delay=0.5, exceptions=_retry_network_exceptions)
    def _post_with_retry():
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except Exception as e:
            # Network-level error
            logger.exception("HTTP POST to %s failed (network/error): %s", url, str(e))
            raise
        return resp
    
    resp = _post_with_retry()
    
    try:
        resp.raise_for_status()
    except _HTTPError as e:
        # Provide the response body and status for debugging upstream failures
        body = None
        try:
            body = resp.text
        except Exception:
            body = str(e)
        short_body = (body[:1000] + '...') if body and len(body) > 1000 else body
        # redact sensitive fields in payload before logging
        redacted_payload = None
        try:
            redacted_payload = _redact_sensitive(payload if isinstance(payload, dict) else {})
        except Exception:
            redacted_payload = 'unavailable'
        safe_headers = _redact_headers(headers)
        logger.error("MPESA HTTP POST error: url=%s status=%s body=%s payload=%s headers=%s", url, resp.status_code, short_body, redacted_payload, safe_headers)
        # safe to use json.dumps here because `json` refers to the module
        raise RuntimeError(f"HTTP POST {url} returned {resp.status_code}: {short_body} | payload: {json.dumps(redacted_payload)}") from e
    return resp


# Simple in-memory token cache (process-local)
_token_cache = {
    'token': None,
    'expiry': 0.0,
}
_token_lock = threading.Lock()


def _current_time():
    return time.time()


def get_access_token():
    # If simulation is enabled, return a dummy token to allow offline testing
    if _simulate_enabled():
        return 'SIMULATED_TOKEN'

    if requests is None:
        raise RuntimeError("The 'requests' package is required to call MPESA APIs")

    # Fast-path: return cached token if valid
    try:
        with _token_lock:
            token = _token_cache.get('token')
            expiry = _token_cache.get('expiry', 0)
            if token and _current_time() < expiry:
                return token
    except Exception:
        # Fail-safe: if locking or cache read fails, proceed to fetch a new token
        pass

    # Fetch a fresh token from MPESA OAuth
    key = settings.MPESA_CONSUMER_KEY
    secret = settings.MPESA_CONSUMER_SECRET
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"

    try:
        resp = _http_get(url, headers={"Authorization": f"Basic {auth}"})
    except RuntimeError as e:
        # Surface a specific auth error so callers can choose a fallback (e.g., simulate)
        logger.error("Failed to fetch MPESA access token: %s", str(e))
        raise MPesaAuthError(str(e))

    try:
        data = resp.json()
    except Exception:
        logger.error("Failed to parse JSON from access token response: %s", resp.text)
        raise RuntimeError("Invalid JSON response when requesting access token")

    token = data.get("access_token")
    if not token:
        logger.error("No access_token in token response: %s", data)
        raise RuntimeError(f"No access_token found in token response: {data}")

    # Determine expiry (seconds). Subtract small buffer to avoid using an expired token.
    try:
        expires_in = int(data.get('expires_in', 3600))
    except Exception:
        expires_in = 3600
    expiry_ts = _current_time() + max(0, expires_in - 10)

    # Store in cache
    try:
        with _token_lock:
            _token_cache['token'] = token
            _token_cache['expiry'] = expiry_ts
    except Exception:
        # best-effort caching; ignore cache failures
        pass

    return token


def _stk_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def _normalize_msisdn(msisdn: str) -> str:
    """Normalize a phone number into Kenyan international format (e.g. 2547XXXXXXXX).

    Accepts numbers like:
    - 0712345678 -> 254712345678
    - +254712345678 -> 254712345678
    - 712345678 -> 254712345678
    - 254712345678 -> 254712345678 (unchanged)
    """
    if not msisdn:
        return msisdn
    s = ''.join(c for c in str(msisdn) if c.isdigit())
    # Strip leading country code zeros
    if s.startswith('0') and len(s) >= 10:
        # replace leading 0 with 254
        s = '254' + s[1:]
    elif s.startswith('7') and len(s) == 9:
        s = '254' + s
    elif s.startswith('+'):
        s = s.lstrip('+')
    # if it already starts with 254 leave unchanged
    return s


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

    # Normalize phone number to expected MSISDN format
    phone_number = _normalize_msisdn(phone_number)

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
    resp = _http_post(url, payload=payload, headers=headers)
    try:
        return resp.json()
    except Exception:
        # In case response is not JSON, raise a helpful error
        body = getattr(resp, 'text', str(resp))
        logger.error('Non-JSON response from STK push: %s', (body or '')[:1000])
        raise RuntimeError('Invalid JSON response from STK push')


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
    resp = _http_post(url, payload=payload, headers=headers)
    try:
        return resp.json()
    except Exception:
        body = getattr(resp, 'text', str(resp))
        logger.error('Non-JSON response from transaction query: %s', (body or '')[:1000])
        raise RuntimeError('Invalid JSON response from transaction query')
