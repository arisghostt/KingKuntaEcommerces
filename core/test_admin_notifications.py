from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Notification


class AdminNotificationEndpointsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username='notif_admin',
            email='notif_admin@test.com',
            password='pass12345',
        )
        self.regular_user = user_model.objects.create_user(
            username='notif_user',
            email='notif_user@test.com',
            password='pass12345',
        )

        Notification.objects.create(
            user=self.regular_user,
            title='Low stock',
            message='Product stock is low',
            level='warning',
        )

    def test_admin_can_list_notifications(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get('/api/admin/notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['results'][0]['username'], self.regular_user.username)

    def test_regular_user_cannot_list_admin_notifications(self):
        self.client.force_authenticate(self.regular_user)

        response = self.client.get('/api/admin/notifications/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
