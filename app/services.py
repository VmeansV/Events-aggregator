import logging
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

from app.client import EventsProviderClient
from app.models import Event, OutboxMessage, Place, Registration, SyncMetadata
from app.paginator import EventsPaginator

logger = logging.getLogger(__name__)


def sync_events_from_provider():
    client = EventsProviderClient()
    sync_info, _ = SyncMetadata.objects.get_or_create(id=1)
    search_from = sync_info.last_changed_at - timedelta(minutes=1)
    try:
        paginator = EventsPaginator(client, changed_at=search_from.date().isoformat())

        last_event_changed_at = search_from
        events_synced = 0

        for event_data in paginator:
            place_data = event_data.pop("place")
            place_defaults = {
                "name": place_data.get("name"),
                "city": place_data.get("city"),
                "address": place_data.get("address"),
                "seats_pattern": place_data.get("seats_pattern"),
            }
            place, _ = Place.objects.update_or_create(id=place_data["id"], defaults=place_defaults)

            provider_changed_at = event_data.get("changed_at")

            event_defaults = {
                "name": event_data.get("name"),
                "place": place,
                "event_time": event_data.get("event_time"),
                "registration_deadline": event_data.get("registration_deadline"),
                "status": event_data.get("status"),
                "number_of_visitors": event_data.get("number_of_visitors", 0),
            }

            event, _ = Event.objects.update_or_create(id=event_data["id"], defaults=event_defaults)

            if provider_changed_at:
                dt = parse_datetime(provider_changed_at)
                if dt and dt > last_event_changed_at:
                    last_event_changed_at = dt

            events_synced += 1

        sync_info.last_changed_at = last_event_changed_at
        sync_info.status = "success"
        sync_info.save()

        return events_synced

    except Exception as e:
        sync_info.status = "error"
        sync_info.save()
        logger.error("Sync failed:", e)
        raise e


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
    client = EventsProviderClient()
    event_id = data.get("event_id")
    seat = data.get("seat")

    # Выполняем запрос к провайдеру
    remote_response = client.register(
        event_id=event_id,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
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

        _outbox_msg = OutboxMessage.objects.create(
            event_type="ticket_purchased",
            payload={
                "ticket_id": provider_ticket_id,
                "email": data.get("email"),
                "fullname": f"{data.get('first_name')} {data.get('last_name')}",
                "message": "Билет куплен",
            },
        )

        # ЗАГЛУШКА
        # transaction.on_commit(
        # lambda: process_outbox_message.delay(outbox_msg.id)
        # )

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
