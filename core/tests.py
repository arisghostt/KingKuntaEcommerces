from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Event


class AdminEventEndpointsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="events_admin",
            email="events_admin@test.com",
            password="pass12345",
        )
        self.regular_user = user_model.objects.create_user(
            username="events_user",
            email="events_user@test.com",
            password="pass12345",
        )

        self.event_one = Event.objects.create(
            title="Quarterly Planning",
            description="Roadmap planning",
            date=date(2026, 3, 10),
            time="09:00 AM",
            location="HQ Room A",
            category="Corporate",
            attendees=25,
            status="upcoming",
        )
        self.event_two = Event.objects.create(
            title="Launch Recap",
            description="Product launch retrospective",
            date=date(2026, 3, 20),
            time="02:00 PM",
            location="HQ Room B",
            category="Product",
            attendees=12,
            status="completed",
        )

    def test_list_events_returns_paginated_payload_with_global_stats(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/events/?page=1&page_size=1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("total", response.data)
        self.assertIn("page", response.data)
        self.assertIn("page_size", response.data)
        self.assertIn("stats", response.data)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 1)
        self.assertEqual(response.data["stats"]["total_events"], 2)
        self.assertEqual(response.data["stats"]["upcoming_count"], 1)
        self.assertEqual(response.data["stats"]["total_attendees"], 37)
        self.assertEqual(response.data["stats"]["categories_count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        # Default sort is date ASC.
        self.assertEqual(response.data["results"][0]["id"], str(self.event_one.id))

    def test_list_events_filters_search_category_status(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(
            "/api/admin/events/?search=room b&category=Product&status=completed"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event_two.id))

    def test_get_event_detail_returns_404_when_missing(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get("/api/admin/events/11111111-1111-1111-1111-111111111111/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Event not found")

    def test_create_event_success(self):
        self.client.force_authenticate(self.admin_user)

        payload = {
            "title": "Client Success Meetup",
            "description": "Top clients meeting",
            "date": "2026-04-05",
            "time": "10:30 AM",
            "location": "Main Hall",
            "category": "Client",
            "attendees": 40,
            "status": "ongoing",
        }
        response = self.client.post("/api/admin/events/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["title"], payload["title"])
        self.assertEqual(response.data["status"], "ongoing")

    def test_create_event_validation_error(self):
        self.client.force_authenticate(self.admin_user)

        payload = {
            "title": "Invalid Event",
            "description": "Invalid attendees",
            "date": "2026-04-05",
            "time": "10:30 AM",
            "location": "Main Hall",
            "category": "Client",
            "attendees": -1,
            "status": "upcoming",
        }
        response = self.client.post("/api/admin/events/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attendees", response.data)

    def test_put_event_updates_all_fields(self):
        self.client.force_authenticate(self.admin_user)

        payload = {
            "title": "Quarterly Planning Updated",
            "description": "Updated desc",
            "date": "2026-03-11",
            "time": "11:00 AM",
            "location": "HQ Room C",
            "category": "Team",
            "attendees": 30,
            "status": "ongoing",
        }
        response = self.client.put(
            f"/api/admin/events/{self.event_one.id}/", payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_one.refresh_from_db()
        self.assertEqual(self.event_one.title, payload["title"])
        self.assertEqual(self.event_one.category, payload["category"])
        self.assertEqual(self.event_one.status, payload["status"])

    def test_patch_event_updates_partial_fields(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            f"/api/admin/events/{self.event_one.id}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_one.refresh_from_db()
        self.assertEqual(self.event_one.status, "completed")

    def test_delete_event_soft_delete(self):
        self.client.force_authenticate(self.admin_user)

        delete_response = self.client.delete(f"/api/admin/events/{self.event_one.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        self.event_one.refresh_from_db()
        self.assertTrue(self.event_one.is_deleted)
        self.assertIsNotNone(self.event_one.deleted_at)

        detail_response = self.client.get(f"/api/admin/events/{self.event_one.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_events_routes_require_admin_role(self):
        self.client.force_authenticate(self.regular_user)

        response = self.client.get("/api/admin/events/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CurrentUserEndpointTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="me_user",
            email="me_user@test.com",
            password="pass12345",
            first_name="Me",
            last_name="User",
        )

    def test_me_endpoint_returns_authenticated_user_payload(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.pk)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["user"]["id"], self.user.pk)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_me_endpoint_requires_authentication(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
