from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from parties.models import Customer
from products.models import Category, Product
from sales.models import SalesOrder, SalesOrderLine


class AdminOrderEndpointsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="orders_admin",
            email="orders_admin@test.com",
            password="pass12345",
        )
        self.regular_user = user_model.objects.create_user(
            username="orders_user",
            email="orders_user@test.com",
            password="pass12345",
        )

        self.customer = Customer.objects.create(
            customer_code="CUST-ORD-1",
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            phone="+33123456789",
            address={"street": "12 Rue A", "city": "Paris", "country": "France"},
            status="active",
        )

        self.category = Category.objects.create(name="Orders Test Category")
        self.product = Product.objects.create(
            name="Order Product",
            category=self.category,
            price=Decimal("99.99"),
            stock=10,
            status="active",
            sku="ORD-PROD-001",
        )

        self.order_pending = SalesOrder.objects.create(
            order_number="SO-ADMIN-001",
            customer=self.customer,
            order_date=date(2026, 2, 20),
            status="DRAFT",
            tax_amount=Decimal("10.00"),
            subtotal=Decimal("100.00"),
            total_amount=Decimal("110.00"),
        )
        self.order_delivered = SalesOrder.objects.create(
            order_number="SO-ADMIN-002",
            customer=self.customer,
            order_date=date(2026, 2, 21),
            status="DELIVERED",
            tax_amount=Decimal("5.00"),
            subtotal=Decimal("50.00"),
            total_amount=Decimal("55.00"),
        )

        SalesOrderLine.objects.create(
            sales_order=self.order_pending,
            product=self.product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("50.00"),
            line_total=Decimal("100.00"),
            discount_percent=Decimal("0.00"),
        )

    def test_list_orders_admin_with_filters(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(
            "/api/admin/orders/",
            {
                "search": "alice@example.com",
                "status": "pending",
                "date": "2026-02-20",
                "page": 1,
                "page_size": 10,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        item = response.data["results"][0]
        self.assertEqual(item["id"], str(self.order_pending.id))
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["items"], 1)

    def test_list_orders_invalid_date_returns_400(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/orders/?date=26-02-2026")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid date format. Expected YYYY-MM-DD.")

    def test_list_orders_requires_admin_role(self):
        self.client.force_authenticate(self.regular_user)

        response = self.client.get("/api/admin/orders/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_order_detail(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(f"/api/admin/orders/{self.order_pending.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.order_pending.id))
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["customer"], "Alice Martin")
        self.assertIn("shipping_address", response.data)
        self.assertIn("billing_address", response.data)
        self.assertIn("payment_method", response.data)
        self.assertIn("tracking_number", response.data)

    def test_get_order_detail_not_found(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/orders/11111111-1111-1111-1111-111111111111/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Order not found")

    def test_patch_order_status_valid_transition(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            f"/api/admin/orders/{self.order_pending.id}/status/",
            {"status": "processing"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order_pending.refresh_from_db()
        self.assertEqual(self.order_pending.status, "CONFIRMED")
        self.assertEqual(response.data["status"], "processing")

    def test_patch_order_status_invalid_transition(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            f"/api/admin/orders/{self.order_pending.id}/status/",
            {"status": "shipped"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid status transition", response.data["error"])

    def test_patch_order_status_delivered_to_cancelled_invalid(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            f"/api/admin/orders/{self.order_delivered.id}/status/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("delivered", response.data["error"].lower())

    def test_refund_order_success_partial(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(
            f"/api/admin/orders/{self.order_pending.id}/refund/",
            {"reason": "Damaged item", "amount": "25.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["amount"], 25.0)
        self.assertTrue(str(response.data["refund_id"]).startswith("RFD-"))

    def test_refund_order_amount_exceeds_total_returns_400(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(
            f"/api/admin/orders/{self.order_pending.id}/refund/",
            {"amount": "999.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Refund amount cannot exceed order total.")
