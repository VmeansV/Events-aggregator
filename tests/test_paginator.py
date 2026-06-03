from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from app.models import Event, Place
from app.pagination import EventPagination


# 1. Интеграционные тесты
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
        self.page_size = getattr(EventPagination, "page_size", 20)

    def test_pagination_multi_page(self):
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
        self.assertIsNotNone(response.data.get("next"))
        self.assertEqual(len(response.data["results"]), self.page_size)

    def test_pagination_single_page(self):
        count_to_create = 5
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
        self.assertEqual(len(response.data["results"]), count_to_create)
        self.assertIsNone(response.data.get("next"))

    def test_pagination_empty_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["results"], [])


# 2. Юнит-тесты для класса
class EventsPaginatorUnitTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.paginator = EventPagination()
        self.place = Place.objects.create(name="P", city="C", address="A", seats_pattern="A1-10")
        for i in range(5):
            Event.objects.create(
                name=f"E{i}",
                place=self.place,
                event_time=timezone.now(),
                registration_deadline=timezone.now(),
                number_of_visitors=0,
            )
        self.queryset = Event.objects.all().order_by("id")

    def test_paginator_attributes(self):
        self.assertTrue(hasattr(self.paginator, "page_size"))

    def test_get_paginated_response_structure(self):
        factory_request = self.factory.get("/")
        # Важный фикс: оборачиваем в DRF Request
        request = Request(factory_request)

        page = self.paginator.paginate_queryset(self.queryset, request)
        response = self.paginator.get_paginated_response(page)

        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("results", response.data)
