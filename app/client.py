import logging
from urllib.parse import urljoin

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class EventsProviderClient:
    def __init__(self):
        self.base_url = settings.EVENTS_PROVIDER_URL
        self.lms_key = settings.LMS_API_KEY
        self.headers = {"X-API-Key": self.lms_key, "Content-Type": "application/json"}
        self.timeout = 10.0

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

        try:
            response = httpx.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error fetching events page: %s", e)
            raise

    def get_seats(self, event_id):
        url = self._get_url(f"events/{event_id}/seats/")
        try:
            response = httpx.get(
                url, headers=self.headers, timeout=self.timeout, follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error fetching seats: %s", e)
            raise

    def register(self, event_id, first_name, last_name, email, seat):
        url = self._get_url(f"events/{event_id}/register/")
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        try:
            response = httpx.post(
                url, json=payload, headers=self.headers, timeout=self.timeout, follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error during registration: %s", e)
            raise

    def unregister(self, event_id, ticket_id):
        url = self._get_url(f"events/{event_id}/unregister/")
        payload = {"ticket_id": str(ticket_id)}
        try:
            response = httpx.request(
                "DELETE",
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error during unregistration: %s", e)
            raise
