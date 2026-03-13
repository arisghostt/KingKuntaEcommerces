import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from inventory.models import StockMovement
from products.models import Category, Product


class AdminInventoryEndpointsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="inventory_admin",
            email="inventory_admin@test.com",
            password="pass12345",
        )
        self.regular_user = user_model.objects.create_user(
            username="inventory_user",
            email="inventory_user@test.com",
            password="pass12345",
        )

        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Wireless Screen",
            category=self.category,
            price=Decimal("99.99"),
            stock=10,
            current_stock=10,
            min_stock=6,
            status="active",
            rating=Decimal("4.0"),
        )
        self.out_product = Product.objects.create(
            name="Empty Product",
            category=self.category,
            price=Decimal("15.00"),
            stock=0,
            current_stock=0,
            min_stock=4,
            status="active",
            rating=Decimal("4.0"),
        )

    def test_inventory_stats_and_movements_admin(self):
        self.client.force_authenticate(self.admin_user)
        now = timezone.now()

        movement_in = StockMovement.objects.create(
            product=self.product,
            type="in",
            quantity=5,
            reason="Purchase",
            created_by=self.admin_user,
            current_stock_after=15,
        )
        movement_out = StockMovement.objects.create(
            product=self.product,
            type="out",
            quantity=3,
            reason="Sale",
            created_by=self.admin_user,
            current_stock_after=12,
        )
        StockMovement.objects.filter(pk=movement_in.pk).update(date=now - timedelta(days=1))
        StockMovement.objects.filter(pk=movement_out.pk).update(date=now)

        stats_response = self.client.get("/api/admin/inventory/stats/")
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertIn("total_products", stats_response.data)
        self.assertIn("stock_in_month", stats_response.data)
        self.assertIn("low_stock_count", stats_response.data)

        movements_response = self.client.get(
            "/api/admin/inventory/movements/?type=out&search=wireless"
        )
        self.assertEqual(movements_response.status_code, status.HTTP_200_OK)
        self.assertEqual(movements_response.data["count"], 1)
        self.assertEqual(movements_response.data["results"][0]["type"], "out")

    def test_create_movement_and_reject_insufficient_stock(self):
        self.client.force_authenticate(self.admin_user)

        reject_response = self.client.post(
            "/api/admin/inventory/movements/",
            {
                "product_id": str(self.product.id),
                "type": "out",
                "quantity": 999,
                "reason": "Sale",
            },
            format="json",
        )
        self.assertEqual(reject_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            reject_response.data["error"],
            "Insufficient stock for this movement.",
        )

        create_response = self.client.post(
            "/api/admin/inventory/movements/",
            {
                "product_id": str(self.product.id),
                "type": "in",
                "quantity": 4,
                "reason": "Purchase",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 14)
        self.assertEqual(self.product.stock, 14)

    def test_alerts_restock_and_export(self):
        self.client.force_authenticate(self.admin_user)

        alerts_response = self.client.get("/api/admin/inventory/alerts/?status=all")
        self.assertEqual(alerts_response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", alerts_response.data)
        self.assertIn("items", alerts_response.data)
        self.assertGreaterEqual(alerts_response.data["summary"]["out_of_stock"], 1)

        restock_response = self.client.patch(
            f"/api/admin/inventory/alerts/{self.out_product.id}/restock/",
            {"quantity": 9, "reason": "Quick restock"},
            format="json",
        )
        self.assertEqual(restock_response.status_code, status.HTTP_200_OK)
        self.out_product.refresh_from_db()
        self.assertEqual(self.out_product.current_stock, 9)
        self.assertEqual(self.out_product.stock, 9)

        export_response = self.client.get("/api/admin/inventory/export/?type=all")
        self.assertEqual(export_response.status_code, status.HTTP_200_OK)
        self.assertEqual(export_response["Content-Type"], "text/csv")
        self.assertIn("attachment;", export_response["Content-Disposition"])

        rows = list(csv.reader(export_response.content.decode("utf-8").splitlines()))
        self.assertEqual(
            rows[0], ["Date", "Product", "Category", "Type", "Quantity", "Reason", "Stock After"]
        )

    def test_inventory_admin_endpoints_require_admin_role(self):
        self.client.force_authenticate(self.regular_user)
        response = self.client.get("/api/admin/inventory/stats/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
