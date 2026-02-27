from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from payments.utils import mpesa_api


class MPESATokenTests(TestCase):
    def setUp(self):
        # ensure module-level requests exists as attribute for patching in environments where requests isn't installed
        if not hasattr(mpesa_api, 'requests'):
            mpesa_api.requests = None
        # clear the in-memory token cache before each test to avoid contamination
        mpesa_api._token_cache['token'] = None
        mpesa_api._token_cache['expiry'] = 0.0

    def test_get_access_token_success(self):
        with patch('payments.utils.mpesa_api.requests', new=Mock()) as mock_requests:
            mock_resp = Mock()
            mock_resp.json.return_value = {'access_token': 'tok123'}
            mock_resp.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_resp

            with override_settings(MPESA_CONSUMER_KEY='k', MPESA_CONSUMER_SECRET='s', MPESA_ENV='sandbox'):
                token = mpesa_api.get_access_token()
                self.assertEqual(token, 'tok123')

    def test_get_access_token_no_requests(self):
        # Simulate requests missing by monkeypatching module variable
        orig = mpesa_api.requests
        mpesa_api.requests = None
        try:
            with self.assertRaises(RuntimeError):
                mpesa_api.get_access_token()
        finally:
            mpesa_api.requests = orig

    def test_initiate_stk_push_success(self):
        with patch('payments.utils.mpesa_api.requests', new=Mock()) as mock_requests, \
             patch('payments.utils.mpesa_api.get_access_token', return_value='token'):
            mock_resp = Mock()
            mock_resp.json.return_value = {'ResponseCode': '0', 'CheckoutRequestID': 'CK1', 'MerchantRequestID': 'MR1'}
            mock_resp.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_resp

            with override_settings(MPESA_SHORTCODE='123', MPESA_PASSKEY='pass', MPESA_CALLBACK_URL='https://example.com/cb', MPESA_ENV='sandbox'):
                res = mpesa_api.initiate_stk_push('0712345678', 10, 'ref', 'desc')
                self.assertIn('CheckoutRequestID', res)

    def test_query_transaction_status_no_requests(self):
        orig = mpesa_api.requests
        mpesa_api.requests = None
        try:
            with self.assertRaises(RuntimeError):
                mpesa_api.query_transaction_status('id')
        finally:
            mpesa_api.requests = orig
