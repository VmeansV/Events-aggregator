import uuid
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from app.models import Event, Place, Registration


class IdempotencyTestCase(APITestCase):
    def setUp(self):
        # Создаем зависимости, чтобы не было ошибок внешнего ключа
        self.place = Place.objects.create(
            name="Test Place", city="Moscow", address="Address", seats_pattern="A1-10"
        )
        self.event = Event.objects.create(
            name="Test Event",
            place=self.place,
            event_time=timezone.now() + timezone.timedelta(days=1),
            registration_deadline=timezone.now(),
            number_of_visitors=0,
        )
        try:
            self.url = reverse("ticket-list")
        except:
            self.url = "/api/tickets/"

    @patch("app.services.EventsProviderClient.register")
    def test_idempotent_registration(self, mock_register):
        """Тест: повторный запрос с тем же ключом возвращает тот же билет."""
        ticket_id = str(uuid.uuid4())
        mock_register.return_value = {"ticket_id": ticket_id}

        data = {
            "event_id": str(self.event.id),
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@test.com",
            "seat": "A1",
            "idempotency_key": "unique-key-123",
        }

        # 1. Первый запрос (создание)
        res1 = self.client.post(self.url, data, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mock_register.call_count, 1)

        # 2. Повторный запрос (идемпотентность)
        res2 = self.client.post(self.url, data, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.data["ticket_id"], ticket_id)
        # Проверяем, что провайдер НЕ вызывался второй раз
        self.assertEqual(mock_register.call_count, 1)

    def test_idempotency_conflict(self):
        """Тест: тот же ключ, но другие данные — 409 Conflict."""
        # Сначала создаем одну запись
        Registration.objects.create(
            id=uuid.uuid4(),
            event=self.event,
            first_name="Ivan",
            last_name="Ivanov",
            email="ivan@test.com",
            seat="A1",
            idempotency_key="key-409",
        )

        # Пытаемся использовать тот же ключ для другого места
        data = {
            "event_id": str(self.event.id),
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@test.com",
            "seat": "B99",  # Другое место
            "idempotency_key": "key-409",
        }

        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
