from django.test import TestCase
from django.urls import reverse

# Create your tests here.

class FrontendViewTests(TestCase):
    def test_home_view_status_and_template(self):
        """The home view should return 200 and use the frontend/index.html template."""
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'frontend/index.html')
