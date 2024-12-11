
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory

from graph.views import VitesseDistributionView
from django.test import TestCase, override_settings
from django.conf import settings

@override_settings(MIGRATION_MODULES=settings.MIGRATION_MODULES)

class VitesseDistributionViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = VitesseDistributionView.as_view()

    def test_get_updated_data(self):
        request = self.factory.get(reverse('vitesse_distribution'), {
            'min_distance': '5000',
            'max_distance': '10000'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('total_count', data)
        self.assertIn('loaded_count', data)
        self.assertIn('new_count', data)
        self.assertIn('plot_data', data)


