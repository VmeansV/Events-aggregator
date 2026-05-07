import logging

from .client import EventsProviderClient
from .models import Event, Place, SyncMetadata
from .paginator import EventsPaginator

logger = logging.getLogger(__name__)


def sync_events_from_provider():
    """Логика синхронизации событий из внешнего API в локальную БД"""
    client = EventsProviderClient()

    # 1. Получаем метаданные (или создаем, если их еще нет)
    sync_info, _ = SyncMetadata.objects.get_or_create(id=1)

    # 2. Определяем, с какой даты искать изменения
    search_from = sync_info.last_changed_at

    logger.info(f"Starting sync from {search_from}")

    try:
        # 3. Используем итератор из paginator.py
        paginator = EventsPaginator(client, changed_at=search_from.isoformat())

        last_event_changed_at = search_from
        events_synced = 0

        for event_data in paginator:
            # Вытаскиваем данные площадки и сохраняем её
            place_data = event_data.pop("place")
            place, _ = Place.objects.update_or_create(id=place_data["id"], defaults=place_data)

            # Сохраняем или обновляем само событие
            event, _ = Event.objects.update_or_create(
                id=event_data["id"], defaults={**event_data, "place": place}
            )

            # Запоминаем самое свежее время изменения среди полученных событий
            if event.changed_at > last_event_changed_at:
                last_event_changed_at = event.changed_at

            events_synced += 1

        # 4. Обновляем метаданные после успешного завершения
        sync_info.last_changed_at = last_event_changed_at
        sync_info.status = "success"
        sync_info.save()

        logger.info(f"Sync finished. Added/Updated {events_synced} events.")
        return events_synced

    except Exception as e:
        sync_info.status = "error"
        sync_info.save()
        logger.error(f"Sync failed: {str(e)}")
        raise e
