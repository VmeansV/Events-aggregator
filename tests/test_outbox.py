import uuid
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from app.models import Event, OutboxMessage, Place, Registration
from app.services import create_ticket_registration


class OutboxTestCase(APITestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Arena", city="City", address="Street", seats_pattern="A1-10"
        )
        self.event = Event.objects.create(
            name="Concert",
            place=self.place,
            event_time=timezone.now() + timezone.timedelta(days=1),
            registration_deadline=timezone.now(),
            number_of_visitors=0,
        )

    @patch("app.services.EventsProviderClient.register")
    def test_outbox_record_created(self, mock_register):
        ticket_id = str(uuid.uuid4())
        mock_register.return_value = {"ticket_id": ticket_id}

        data = {
            "event_id": str(self.event.id),
            "first_name": "Test",
            "last_name": "User",
            "email": "test@test.com",
            "seat": "A1",
        }

        create_ticket_registration(data)

        # Проверяем, что записи создались
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(OutboxMessage.objects.count(), 1)

        msg = OutboxMessage.objects.first()
        self.assertEqual(msg.status, "pending")
        self.assertEqual(msg.payload["reference_id"], ticket_id)
