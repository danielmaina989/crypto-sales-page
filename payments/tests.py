from django.test import TestCase


class PaymentsSmokeTest(TestCase):
    def test_status_endpoint(self):
        resp = self.client.get('/payments/status/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'payments app is alive')

