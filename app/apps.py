import asyncio
import os
import threading

from django.apps import AppConfig

from app.outbox_processor import run_outbox_worker


class WorkerConfig(AppConfig):
    name = "app"

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("GUNICORN_STARTED") == "true":
            return

        os.environ["GUNICORN_STARTED"] = "true"

        def start_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_outbox_worker())

        thread = threading.Thread(target=start_loop, daemon=True)
        thread.start()
