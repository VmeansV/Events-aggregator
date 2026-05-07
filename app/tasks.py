import logging

from celery import shared_task

from .services import sync_events_from_provider

logger = logging.getLogger(__name__)


@shared_task(name="sync_events_task")
def daily_sync_task():
    """
    Фоновая задача для периодической синхронизации событий.
    Выполняется раз в день по расписанию.
    """
    logger.info("Фоновая синхронизация: НАЧАЛО")

    try:
        count = sync_events_from_provider()

        logger.info(f"Фоновая синхронизация: УСПЕШНО. Обновлено событий: {count}")
        return f"Synced {count} events"

    except Exception as e:
        logger.error(f"Фоновая синхронизация: ОШИБКА - {str(e)}")
        raise e
