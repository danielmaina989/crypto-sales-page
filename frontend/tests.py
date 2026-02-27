from django.test import TestCase
from django.urls import reverse
import json

# Create your tests here.

class FrontendViewTests(TestCase):
    def test_home_view_status_and_template(self):
        """The home view should return 200 and use the frontend/index.html template."""
        # namespace added for frontend URLs
        resp = self.client.get(reverse('frontend:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'frontend/index.html')

    def test_chat_api_basic_flow(self):
        """POSTing a chat message should return JSON with a reply and intent."""
        url = reverse('frontend:api-chat')
        resp = self.client.post(url, data=json.dumps({'message': 'How do I make a payment?'}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # should include reply and intent fields
        self.assertIn('reply', data)
        self.assertEqual(data.get('intent'), 'payment')

    def test_chat_api_rate_limit(self):
        url = reverse('frontend:api-chat')
        # ensure previous test calls don't pollute rate counter
        from django.core.cache import cache
        cache.clear()
        # hit the endpoint limit times
        for i in range(21):
            resp = self.client.post(url, data=json.dumps({'message': 'test'}), content_type='application/json')
            if i < 20:
                self.assertEqual(resp.status_code, 200)
            else:
                # 21st request should be forbidden
                self.assertEqual(resp.status_code, 403)


class LoggingFilterTests(TestCase):
    def test_phone_mask_filter_masks_numbers(self):
        from core.logging import PhoneMaskFilter
        import logging

        record = logging.LogRecord(name='test', level=logging.INFO, pathname=__file__, lineno=1,
                                   msg='call me on 0712345678 or +254712345678', args=(), exc_info=None)
        filt = PhoneMaskFilter()
        self.assertTrue(filt.filter(record))
        self.assertNotIn('0712345678', record.msg)
        self.assertNotIn('+254712345678', record.msg)
        # check that numbers are replaced by asterisks of same length
        self.assertIn('**********', record.msg)
        self.assertIn('************', record.msg)
        # also verify email and card masking
        record2 = logging.LogRecord(name='test', level=logging.INFO, pathname=__file__, lineno=1,
                                    msg='contact me at user@example.com or card 4111 1111 1111 1111', args=(), exc_info=None)
        filt2 = PhoneMaskFilter()
        filt2.filter(record2)
        self.assertNotIn('user@example.com', record2.msg)
        self.assertNotIn('4111 1111 1111 1111', record2.msg)
        self.assertIn('*****************', record2.msg)
        # ensure request id filter attaches empty id when none set
        from core.logging import RequestIDFilter
        rec3 = logging.LogRecord(name='test', level=logging.INFO, pathname=__file__, lineno=1,
                                 msg='hello', args=(), exc_info=None)
        reqf = RequestIDFilter()
        reqf.filter(rec3)
        self.assertTrue(hasattr(rec3, 'request_id'))
