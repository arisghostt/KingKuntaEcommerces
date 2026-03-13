from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from parties.models import Customer
from sales.models import SalesOrder


class AdminCustomerEndpointsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="pass12345",
        )
        self.regular_user = user_model.objects.create_user(
            username="user_test",
            email="user@test.com",
            password="pass12345",
        )

        self.customer = Customer.objects.create(
            customer_code="CUST-900",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+12345678",
            address={"city": "Paris", "country": "France"},
            is_active=True,
            status="active",
        )
        self.inactive_customer = Customer.objects.create(
            customer_code="CUST-901",
            first_name="Jane",
            last_name="Roe",
            email="jane@example.com",
            is_active=False,
            status="inactive",
        )

        SalesOrder.objects.create(
            order_number="SO-900A",
            customer=self.customer,
            order_date=date(2026, 1, 10),
            status="DELIVERED",
            total_amount="100.00",
        )
        SalesOrder.objects.create(
            order_number="SO-900B",
            customer=self.customer,
            order_date=date(2026, 2, 10),
            status="CONFIRMED",
            total_amount="50.00",
        )

    def test_list_customers_admin(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/customers/?search=john&status=active&sort=orders")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        first_item = response.data["results"][0]
        self.assertEqual(first_item["email"], "john@example.com")
        self.assertEqual(first_item["orders"], 2)
        self.assertEqual(first_item["status"], "active")

    def test_list_customers_requires_admin_role(self):
        self.client.force_authenticate(self.regular_user)

        response = self.client.get("/api/admin/customers/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_customer_detail_with_orders(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(f"/api/admin/customers/{self.customer.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["orders_count"], 2)
        self.assertEqual(len(response.data["orders"]), 2)
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["total_spent"], "150.00")

    def test_patch_customer_status_and_notes(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            f"/api/admin/customers/{self.customer.id}/",
            {"status": "blocked", "notes": "Manual block for fraud check"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.status, "blocked")
        self.assertFalse(self.customer.is_active)
        self.assertEqual(self.customer.notes, "Manual block for fraud check")
        # API normalizes blocked as inactive for frontend compatibility.
        self.assertEqual(response.data["status"], "inactive")

    def test_delete_customer_soft_delete(self):
        self.client.force_authenticate(self.admin_user)

        delete_response = self.client.delete(f"/api/admin/customers/{self.customer.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_deleted)
        self.assertFalse(self.customer.is_active)

        list_response = self.client.get("/api/admin/customers/")
        ids = [item["id"] for item in list_response.data["results"]]
        self.assertNotIn(str(self.customer.id), ids)

    def test_customer_not_found_returns_404(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/customers/11111111-1111-1111-1111-111111111111/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Customer not found")

    def test_list_customers_accepts_legacy_token_header_prefix(self):
        access_token = str(RefreshToken.for_user(self.admin_user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {access_token}")

        response = self.client.get("/api/admin/customers/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
