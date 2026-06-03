import logging
import time
from urllib.parse import urljoin

import httpx
from django.conf import settings

from app.metrics import EVENTS_PROVIDER_DURATION, EVENTS_PROVIDER_REQUEST_TOTAL

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, base_url, timeout=10):
        self.base_url = base_url if base_url.endswith("/") else f"{base_url}/"
        self.timeout = timeout

    def _get_url(self, path):
        return urljoin(self.base_url, path.lstrip("/"))


class EventsProviderClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.EVENTS_PROVIDER_URL)
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": settings.LMS_API_KEY,
        }

    def _get_url(self, path: str) -> str:
        """Вспомогательный метод для безопасной сборки URL."""
        base = self.base_url if self.base_url.endswith("/") else f"{self.base_url}/"
        return urljoin(base, path.lstrip("/"))

    def get_events_page(self, url=None, changed_at=None):
        """Получение страницы событий (используется итератором)"""
        params = None
        if not url:
            url = self._get_url("events/")
            params = {"changed_at": changed_at or "2000-01-01"}

        start_time = time.monotonic()
        status_code = 500

        try:
            response = httpx.get(url, headers=self.headers, params=params, timeout=self.timeout)
            status_code = response.status_code
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if hasattr(e, "response") and e.response:
                status_code = e.response.status_code
            logger.error("Error fetching events page: %s", e)
            raise
        finally:
            duration = time.monotonic() - start_time
            EVENTS_PROVIDER_REQUEST_TOTAL.labels(endpoint="/events", status=status_code).inc()
            EVENTS_PROVIDER_DURATION.labels(endpoint="/events").observe(duration)

    def get_seats(self, event_id):
        url = self._get_url(f"events/{event_id}/seats/")

        start_time = time.monotonic()
        status_code = 500

        try:
            response = httpx.get(
                url, headers=self.headers, timeout=self.timeout, follow_redirects=True
            )
            status_code = response.status_code
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if hasattr(e, "response") and e.response:
                status_code = e.response.status_code
            logger.error("Error fetching seats: %s", e)
            raise
        finally:
            duration = time.monotonic() - start_time
            EVENTS_PROVIDER_REQUEST_TOTAL.labels(endpoint="/seats", status=status_code).inc()
            EVENTS_PROVIDER_DURATION.labels(endpoint="/seats").observe(duration)

    def register(self, event_id, first_name, last_name, email, seat):
        url = self._get_url(f"events/{event_id}/register/")
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}

        start_time = time.monotonic()
        status_code = 500

        try:
            response = httpx.post(
                url, json=payload, headers=self.headers, timeout=self.timeout, follow_redirects=True
            )
            status_code = response.status_code
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if hasattr(e, "response") and e.response:
                status_code = e.response.status_code
            logger.error("Error during registration: %s", e)
            raise
        finally:
            duration = time.monotonic() - start_time
            EVENTS_PROVIDER_REQUEST_TOTAL.labels(endpoint="/registration", status=status_code).inc()
            EVENTS_PROVIDER_DURATION.labels(endpoint="/registration").observe(duration)

    def unregister(self, event_id, ticket_id):
        url = self._get_url(f"events/{event_id}/unregister/")
        payload = {"ticket_id": str(ticket_id)}

        start_time = time.monotonic()
        status_code = 500

        try:
            response = httpx.request(
                "DELETE",
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
            status_code = response.status_code
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if hasattr(e, "response") and e.response:
                status_code = e.response.status_code
            logger.error("Error during unregistration: %s", e)
            raise
        finally:
            duration = time.monotonic() - start_time
            EVENTS_PROVIDER_REQUEST_TOTAL.labels(endpoint="/registration", status=status_code).inc()
            EVENTS_PROVIDER_DURATION.labels(endpoint="/registration").observe(duration)


class CapashinoClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.CAPASHINO_URL)
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": settings.LMS_API_KEY,
        }

    def send_notification(self, payload):
        url = self._get_url("api/notifications")

        try:
            response = httpx.post(url, json=payload, headers=self.headers, timeout=self.timeout)

            if response.status_code == 409:
                return response.json()

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error("Capashino API error: %s", e)
            raise
