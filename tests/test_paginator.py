from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from app.models import Event, Place
from app.pagination import EventPagination


class EventPaginationTestCase(APITestCase):
    def setUp(self):
        try:
            self.url = reverse("event-list")
        except Exception:
            self.url = "/api/events/"

        self.place = Place.objects.create(
            name="Test Stadium", city="Moscow", address="Luzhniki, 1", seats_pattern="A1-100"
        )
        self.now = timezone.now()

        self.page_size = getattr(EventPagination, "page_size", 10)

    def test_pagination_multi_page(self):
        """Тест: несколько страниц. Создаем объектов больше, чем размер одной страницы."""
        count_to_create = self.page_size + 1

        for i in range(count_to_create):
            Event.objects.create(
                name=f"Event {i}",
                place=self.place,
                event_time=self.now + timedelta(days=2),
                registration_deadline=self.now + timedelta(days=1),
                number_of_visitors=0,
                status=Event.Status.PUBLISHED,
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], count_to_create)

        self.assertIsNotNone(
            response.data.get("next"),
            msg=f"Next page link is missing. Page size is {self.page_size}, created {count_to_create} items.",
        )
        self.assertEqual(len(response.data["results"]), self.page_size)

    def test_pagination_single_page(self):
        """Тест: одна страница. Создаем ровно столько, сколько влезает на одну страницу."""
        count_to_create = self.page_size

        for i in range(count_to_create):
            Event.objects.create(
                name=f"Single Event {i}",
                place=self.place,
                event_time=self.now + timedelta(days=2),
                registration_deadline=self.now + timedelta(days=1),
                number_of_visitors=0,
                status=Event.Status.PUBLISHED,
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], count_to_create)
        self.assertIsNone(response.data.get("next"))
        self.assertEqual(len(response.data["results"]), count_to_create)

    def test_pagination_empty_results(self):
        """Тест: пустой ответ."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
