import json
from unittest import mock
from django.test import TestCase
from payments.utils import mpesa_api

class MPesaTokenTests(TestCase):
    @mock.patch('payments.utils.mpesa_api.requests.get')
    def test_get_access_token_success(self, mock_get):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = {'access_token': 'abc123', 'expires_in': 3600}
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        token = mpesa_api.get_access_token()
        self.assertEqual(token, 'abc123')

    @mock.patch('payments.utils.mpesa_api.requests.get')
    def test_get_access_token_invalid_json(self, mock_get):
        mock_resp = mock.Mock()
        mock_resp.text = '<html>Incapsula</html>'
        mock_resp.json.side_effect = ValueError('No JSON')
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with self.assertRaises(RuntimeError):
            mpesa_api.get_access_token()

    @mock.patch('payments.utils.mpesa_api.requests.get')
    def test_get_access_token_http_error(self, mock_get):
        mock_resp = mock.Mock()
        mock_resp.raise_for_status.side_effect = mpesa_api._HTTPError('403')
        mock_resp.status_code = 403
        mock_resp.text = 'Forbidden'
        mock_get.return_value = mock_resp

        with self.assertRaises(RuntimeError):
            mpesa_api.get_access_token()

