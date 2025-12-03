import base64
import requests
import time

# --- Sandbox credentials (from your earlier .env) ---
MPESA_CONSUMER_KEY = "riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk"
MPESA_CONSUMER_SECRET = "fXRp0DR8huY76Bsjog15rX2CAcZ27i19dyu3AtYGYzHorvHWIXDJKUqJCqtGAxsn"

OAUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

# Encode key:secret to Base64
key_secret = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
auth_header = base64.b64encode(key_secret.encode()).decode()
headers = {"Authorization": f"Basic {auth_header}"}

max_attempts = 5
delay_seconds = 5

for attempt in range(1, max_attempts + 1):
    try:
        response = requests.get(OAUTH_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ Access token retrieved successfully!")
        print("Access Token:", data.get("access_token"))
        print("Expires in:", data.get("expires_in"))
        break  # success, exit loop
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Attempt {attempt} HTTP error: {http_err}")
        if response is not None:
            print(response.status_code)
            print(response.text[:1000])  # print only first 1000 chars
    except Exception as e:
        print(f"❌ Attempt {attempt} other error: {e}")

    if attempt < max_attempts:
        print(f"⏳ Retrying in {delay_seconds} seconds...")
        time.sleep(delay_seconds)
    else:
        print("❌ All attempts failed. Check your keys or sandbox status.")

