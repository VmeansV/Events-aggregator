import logging

from .client import EventsProviderClient
from .models import Event, Place, SyncMetadata
from .paginator import EventsPaginator

logger = logging.getLogger(__name__)


def sync_events_from_provider():
    client = EventsProviderClient()
    sync_info, _ = SyncMetadata.objects.get_or_create(id=1)
    search_from = sync_info.last_changed_at

    try:
        # Передаем дату в формате ISO
        paginator = EventsPaginator(client, changed_at=search_from.isoformat())

        last_event_changed_at = search_from
        events_synced = 0

        for event_data in paginator:
            # 1. Обработка Площадки
            place_data = event_data.pop("place")
            # Явно перечисляем поля, чтобы не пытаться записать лишнее или системное
            place_defaults = {
                "name": place_data.get("name"),
                "city": place_data.get("city"),
                "address": place_data.get("address"),
                "seats_pattern": place_data.get("seats_pattern"),
            }
            place, _ = Place.objects.update_or_create(id=place_data["id"], defaults=place_defaults)

            # 2. Обработка События
            # Запоминаем дату изменения от Провайдера, чтобы обновить метаданные
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

            # Обновляем метку времени для следующей синхронизации
            if provider_changed_at:
                # Превращаем строку в объект даты для сравнения
                from django.utils.dateparse import parse_datetime

                dt = parse_datetime(provider_changed_at)
                if dt and dt > last_event_changed_at:
                    last_event_changed_at = dt

            events_synced += 1

        # 3. Успешное завершение
        sync_info.last_changed_at = last_event_changed_at
        sync_info.status = "success"
        sync_info.save()

        return events_synced

    except Exception as e:
        sync_info.status = "error"
        sync_info.save()
        logger.error(f"Sync failed: {str(e)}")
        raise e
