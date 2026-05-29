import asyncio
import logging

from asgiref.sync import sync_to_async
from django.apps import apps

from app.client import CapashinoClient

logger = logging.getLogger(__name__)


async def run_outbox_worker():
    """Фоновая корутина, которая проверяет базу раз в 5 секунд."""

    OutboxMessage = apps.get_model("app", "OutboxMessage")
    client = CapashinoClient()

    while True:
        try:
            messages = await sync_to_async(list)(
                OutboxMessage.objects.filter(status="pending").order_by("created_at")[:10]
            )

            for msg in messages:
                try:
                    await sync_to_async(client.send_notification)(msg.payload)
                    msg.status = "processed"
                    await sync_to_async(msg.save)()
                    logger.info("Outbox message %s processed by coroutine", msg.id)

                except Exception as e:
                    logger.error("Failed to process outbox %s: %s", msg.id, e)

            await asyncio.sleep(5)
        except Exception as e:
            logger.error("Global outbox worker error: %s", e)
            await asyncio.sleep(10)
