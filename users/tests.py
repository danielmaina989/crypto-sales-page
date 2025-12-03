from django.test import TestCase


class UsersSmokeTest(TestCase):
    def test_profile_endpoint(self):
        resp = self.client.get('/users/profile/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'users app alive')

