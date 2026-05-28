import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from app.client import CapashinoClient
from app.models import OutboxMessage
from app.services import sync_events_from_provider

logger = logging.getLogger(__name__)


@shared_task()
def daily_sync_task():
    """
    Фоновая задача для периодической синхронизации событий.
    Выполняется раз в день по расписанию.
    """
    logger.info("Фоновая синхронизация: НАЧАЛО")

    try:
        count = sync_events_from_provider()

        logger.info("Фоновая синхронизация: УСПЕШНО. Обновлено событий: %s", count)
        return f"Synced {count} events"

    except Exception as e:
        logger.error("Фоновая синхронизация: ОШИБКА - %s", e)
        raise e


@shared_task(bind=True, max_retries=10)
def process_outbox_message(self, message_id):
    try:
        msg = OutboxMessage.objects.get(id=message_id, status="pending")
    except OutboxMessage.DoesNotExist:
        return

    client = CapashinoClient()

    try:
        client.send_notification(msg.payload)

        msg.status = "processed"
        msg.save()
        logger.info("Message %s successfully sent to Capashino", message_id)
    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            logger.error("Message %s failed after maximum retries", message_id)
            msg.status = "failed"
            msg.save()
