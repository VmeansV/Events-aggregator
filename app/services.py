import logging
import uuid

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404

from app.client import EventsProviderClient
from app.exceptions import IdempotencyConflictError
from app.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL
from app.models import Event, OutboxMessage, Registration
from app.serializers import RegistrationSerializer

logger = logging.getLogger(__name__)


def get_event_seats_with_cache(event_id):
    """Логика получения мест с кэшированием."""
    event = get_object_or_404(Event, id=event_id)

    cache_key = f"seats_{event.id}"
    cached_seats = cache.get(cache_key)

    if cached_seats is not None:
        CACHE_HITS_TOTAL.inc()
        return {"event_id": str(event.id), "available_seats": cached_seats}

    CACHE_MISSES_TOTAL.inc()

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
        existing_reg = Registration.objects.filter(
            idempotency_key=client_key, status=Registration.Status.RESERVED
        ).first()

        if existing_reg:
            if (
                str(existing_reg.event_id) != str(event_id)
                or existing_reg.seat != seat
                or existing_reg.email != email
            ):
                raise IdempotencyConflictError("Key already used by other data")

            return RegistrationSerializer(existing_reg).data

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
        reg = Registration.objects.create(
            id=provider_ticket_id,
            event_id=event_id,
            seat=seat,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=email,
            idempotency_key=client_key,
            status=Registration.Status.RESERVED,
        )

        outbox_id = uuid.uuid4()
        OutboxMessage.objects.create(
            id=outbox_id,
            event_type="ticket_purchased",
            payload={
                "message": "Билет куплен",
                "reference_id": str(provider_ticket_id),
                "idempotency_key": str(outbox_id),
            },
        )

    return RegistrationSerializer(reg).data


def cancel_ticket_registration(ticket_id):
    """Бизнес-логика отмены регистрации."""
    reg = Registration.objects.filter(id=ticket_id).select_related("event").first()

    if not reg:
        return False, "Ticket not found locally"

    if reg.status == Registration.Status.CANCELLED:
        return True, None

    client = EventsProviderClient()

    with transaction.atomic():
        # Отменяем у провайдера
        client.unregister(event_id=reg.event.id, ticket_id=ticket_id)
        # Удаляем у себя
        reg.status = Registration.Status.CANCELLED
        reg.save()

    return True, None
