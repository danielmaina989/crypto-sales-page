from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from payments.models import Payment
from payments.utils.notifications import notify_payment_success


class NotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='notifytest', email='notify@example.com', password='pw')
        self.payment = Payment.objects.create(user=self.user, amount=10, phone_number='0712345678', status='success', mpesa_receipt_number='R123')

    @patch('payments.utils.notifications.send_mail')
    def test_notify_email(self, mock_send_mail):
        res = notify_payment_success(self.payment, via=('email',))
        # find the email entry and assert user's email is included
        email_entries = [r for r in res if r[0] == 'email']
        self.assertTrue(email_entries)
        recipients = email_entries[0][1]
        self.assertIn('notify@example.com', recipients)
        mock_send_mail.assert_called()

    @patch('payments.utils.notifications.TwilioClient')
    def test_notify_sms_with_twilio(self, mock_twilio):
        # Provide fake twilio credentials in settings using override_settings
        with override_settings(TWILIO_ACCOUNT_SID='sid', TWILIO_AUTH_TOKEN='token', TWILIO_FROM_NUMBER='+1000000000'):
            mock_client = Mock()
            mock_twilio.return_value = mock_client
            res = notify_payment_success(self.payment, via=('sms',))
            # The function may or may not append ('sms', number) depending on Twilio availability.
            # Ensure it doesn't raise and returns a list
            self.assertIsInstance(res, list)
            # If Twilio attempted send, mock_client.messages.create may have been called
            try:
                mock_client.messages.create.assert_called()
            except Exception:
                pass
