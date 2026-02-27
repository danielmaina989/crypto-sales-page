from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import json
from payments.models import Payment
from payments.utils.mpesa_api import (
    initiate_stk_push, 
    get_access_token,
    query_transaction_status,
    MPesaAuthError
)

User = get_user_model()


class MPESAPaymentFlowTests(TestCase):
    """Test suite for complete MPESA payment flows"""

    def setUp(self):
        """Set up test user and payment"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='test_passkey',
        MPESA_CALLBACK_URL='https://example.com/callback'
    )
    def test_stk_push_initiation_success(self):
        """Test successful STK push initiation"""
        with patch('payments.utils.mpesa_api.get_access_token', return_value='test_token'), \
             patch('payments.utils.mpesa_api.requests') as mock_requests:
            
            mock_resp = Mock()
            mock_resp.json.return_value = {
                'ResponseCode': '0',
                'ResponseDescription': 'Success. Request accepted for processing',
                'CheckoutRequestID': 'WS_CO_DMZ_123456_2023',
                'MerchantRequestID': 'MR_123456_2023'
            }
            mock_resp.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_resp
            
            result = initiate_stk_push(
                phone_number='254712345678',
                amount=1000,
                account_ref='TEST-001',
                description='Test payment'
            )
            
            self.assertEqual(result['ResponseCode'], '0')
            self.assertIn('CheckoutRequestID', result)
            self.assertIn('MerchantRequestID', result)
    
    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='test_passkey',
        MPESA_CALLBACK_URL='https://example.com/callback'
    )
    def test_stk_push_stores_payment_details(self):
        """Test that STK push response stores payment details correctly"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            phone_number='254712345678',
            account_ref='BUY-001',
            description='Buy crypto',
            status='pending'
        )
        
        with patch('payments.utils.mpesa_api.get_access_token', return_value='test_token'), \
             patch('payments.utils.mpesa_api.requests') as mock_requests:
            
            mock_resp = Mock()
            mock_resp.json.return_value = {
                'ResponseCode': '0',
                'CheckoutRequestID': 'CK_TEST_123',
                'MerchantRequestID': 'MR_TEST_123'
            }
            mock_resp.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_resp
            
            result = initiate_stk_push(
                phone_number=payment.phone_number,
                amount=int(float(payment.amount)),
                account_ref=payment.account_ref,
                description=payment.description
            )
            
            # Update payment with response
            payment.checkout_request_id = result['CheckoutRequestID']
            payment.merchant_request_id = result['MerchantRequestID']
            payment.callback_raw_data = result
            payment.save()
            
            # Verify payment was updated
            payment.refresh_from_db()
            self.assertEqual(payment.checkout_request_id, 'CK_TEST_123')
            self.assertEqual(payment.merchant_request_id, 'MR_TEST_123')
            self.assertEqual(payment.status, 'pending')
    
    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox'
    )
    def test_get_access_token_success(self):
        """Test successful access token retrieval"""
        with patch('payments.utils.mpesa_api.requests') as mock_requests:
            mock_resp = Mock()
            mock_resp.json.return_value = {'access_token': 'test_token_response'}
            mock_resp.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_resp
            
            token = get_access_token()
            self.assertEqual(token, 'test_token_response')
    
    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='test_passkey',
        MPESA_CALLBACK_URL='https://example.com/callback'
    )
    def test_stk_push_with_invalid_phone(self):
        """Test STK push with invalid phone number handling"""
        with patch('payments.utils.mpesa_api.get_access_token', return_value='test_token'), \
             patch('payments.utils.mpesa_api.requests') as mock_requests:
            
            mock_resp = Mock()
            mock_resp.json.return_value = {
                'ResponseCode': '400',
                'ResponseDescription': 'Invalid phone number'
            }
            mock_resp.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_resp
            
            result = initiate_stk_push(
                phone_number='invalid',
                amount=1000,
                account_ref='TEST-001',
                description='Test payment'
            )
            
            # Response code indicates error
            self.assertEqual(result['ResponseCode'], '400')
    
    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox'
    )
    def test_access_token_missing_requests(self):
        """Test handling when requests library is not available"""
        import payments.utils.mpesa_api as mpesa_module
        
        original_requests = mpesa_module.requests
        try:
            mpesa_module.requests = None
            
            with self.assertRaises(RuntimeError) as context:
                get_access_token()
            
            self.assertIn('requests', str(context.exception).lower())
        finally:
            mpesa_module.requests = original_requests
    
    def test_payment_creation_for_buy_flow(self):
        """Test payment record creation for buy flow"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50000.00'),
            phone_number='254712345678',
            account_ref='BUY-TRADE-123',
            description='Buy 0.5 BTC',
            status='pending'
        )
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, Decimal('50000.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.account_ref, 'BUY-TRADE-123')
    
    def test_payment_status_transitions(self):
        """Test payment status transitions"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            phone_number='254712345678',
            status='pending'
        )
        
        # Simulate successful MPESA callback
        payment.status = 'success'
        payment.mpesa_receipt_number = 'SAF116P6C8Z'
        payment.save()
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')
        self.assertEqual(payment.mpesa_receipt_number, 'SAF116P6C8Z')
        
        # Test failed payment
        payment2 = Payment.objects.create(
            user=self.user,
            amount=Decimal('2000.00'),
            phone_number='254712345678',
            status='failed',
            error_code='1001',
            error_message='Insufficient balance'
        )
        
        self.assertEqual(payment2.status, 'failed')
        self.assertEqual(payment2.error_code, '1001')
    
    def test_payment_multiple_users(self):
        """Test that payments are correctly isolated per user"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        payment1 = Payment.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            phone_number='254712345678',
            status='pending'
        )
        
        payment2 = Payment.objects.create(
            user=user2,
            amount=Decimal('2000.00'),
            phone_number='254712345679',
            status='success'
        )
        
        # User 1 should only see their payment
        user1_payments = Payment.objects.filter(user=self.user)
        self.assertEqual(user1_payments.count(), 1)
        self.assertEqual(user1_payments.first().amount, Decimal('1000.00'))
        
        # User 2 should only see their payment
        user2_payments = Payment.objects.filter(user=user2)
        self.assertEqual(user2_payments.count(), 1)
        self.assertEqual(user2_payments.first().amount, Decimal('2000.00'))

    @override_settings(
        MPESA_CONSUMER_KEY='test_key',
        MPESA_CONSUMER_SECRET='test_secret',
        MPESA_ENV='sandbox',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='test_passkey',
        MPESA_CALLBACK_URL='https://example.com/callback'
    )
    def test_celery_poll_enqueued(self):
        """Initiating a payment should enqueue the poll_payment_status task when celery is available"""
        from payments.views import initiate
        from payments import tasks as payments_tasks

        # ensure simulation disabled and patch network calls
        with patch('payments.views.initiate._mpesa_api._simulate_enabled', return_value=False), \
             patch('payments.views.initiate.initiate_stk_push') as mock_stk, \
             patch('payments.views.initiate.get_access_token', return_value='fake_token'), \
             patch.object(payments_tasks.poll_payment_status, 'delay') as mock_delay:
            mock_stk.return_value = {'ResponseCode': '0', 'CheckoutRequestID': 'CK123', 'MerchantRequestID': 'MR123'}
            # perform request via test client
            resp = self.client.post('/payments/initiate/', data=json.dumps({
                'phone_number': '254712345678',
                'amount': 1000
            }), content_type='application/json')
            self.assertEqual(resp.status_code, 200)
            # verify delay was called at least once with payment id
            self.assertTrue(mock_delay.called)
            called_args = mock_delay.call_args[0]
            self.assertIsNotNone(called_args[0])  # payment id
            # optional: ensure attempt parameters passed
            self.assertIn('attempts', mock_delay.call_args[1])
