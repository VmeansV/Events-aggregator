import logging
import uuid

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404

from app.client import EventsProviderClient
from app.exceptions import IdempotencyConflictError
from app.models import Event, OutboxMessage, Registration
from app.tasks import process_outbox_message

logger = logging.getLogger(__name__)


def get_event_seats_with_cache(event_id):
    """Логика получения мест с кэшированием."""
    event = get_object_or_404(Event, id=event_id)

    cache_key = f"seats_{event.id}"
    cached_seats = cache.get(cache_key)

    if cached_seats is not None:
        return {"event_id": str(event.id), "available_seats": cached_seats}

    client = EventsProviderClient()
    remote_data = client.get_seats(event.id)
    available_seats = remote_data.get("seats", [])

    cache.set(cache_key, available_seats, timeout=30)
    return {"event_id": str(event.id), "available_seats": available_seats}


def create_ticket_registration(data):
    """Бизнес-логика покупки билета."""
    client_key = data.get("idempotency_key")
    event_id = data.get("event_id")
    seat = data.get("seat")
    email = data.get("email")

    if client_key:
        existing_reg = Registration.objects.filter(idempotency_key=client_key).first()

        if existing_reg:
            if (
                str(existing_reg.event_id) == str(event_id)
                or existing_reg.seat == seat
                or existing_reg.email == email
            ):
                raise IdempotencyConflictError("Key already used by other data")

        return {
            "ticket_id": str(existing_reg.id),
            "event_id": str(existing_reg.event_id),
            "seat": existing_reg.seat,
            "first_name": existing_reg.first_name,
            "last_name": existing_reg.last_name,
        }

    # Выполняем запрос к провайдеру
    client = EventsProviderClient()
    remote_response = client.register(
        event_id=event_id,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=email,
        seat=seat,
    )

    provider_ticket_id = remote_response.get("ticket_id")

    # Сохраняем в нашу БД
    with transaction.atomic():
        Registration.objects.update_or_create(
            id=provider_ticket_id,
            defaults={
                "event_id": event_id,
                "seat": seat,
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "email": data.get("email"),
            },
        )

        outbox_id = uuid.uuid4()

        outbox_msg = OutboxMessage.objects.create(
            id=outbox_id,
            event_type="ticket_purchased",
            payload={
                "ticket_id": provider_ticket_id,
                "email": data.get("email"),
                "fullname": f"{data.get('first_name')} {data.get('last_name')}",
                "message": "Билет куплен",
                "idempotency_key": outbox_id,
            },
        )

        transaction.on_commit(lambda: process_outbox_message.delay(outbox_msg.id))

    return remote_response


def cancel_ticket_registration(ticket_id):
    """Бизнес-логика отмены регистрации."""
    reg = Registration.objects.filter(id=ticket_id).select_related("event").first()
    if not reg:
        return False, "Ticket not found locally"

    client = EventsProviderClient()

    with transaction.atomic():
        # Отменяем у провайдера
        client.unregister(event_id=reg.event.id, ticket_id=ticket_id)
        # Удаляем у себя
        reg.delete()

    return True, None
