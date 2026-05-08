import logging
import os

import httpx

logger = logging.getLogger(__name__)


class EventsProviderClient:
    def __init__(self):
        # 1. URL
        self.base_url = os.getenv(
            "EVENTS_PROVIDER_URL",
            "http://student-system-events-provider-web.student-system-events-provider.svc:8000/api",
        ).rstrip("/")

        # 2. API-ключ. Пробуем три варианта, чтобы точно не получить None
        # Сначала системный API_KEY, потом LMS_API_KEY, если нет - пустая строка
        env_key = os.getenv("API_KEY") or os.getenv("LMS_API_KEY")
        self.api_key = str(env_key) if env_key is not None else ""

        # Убедимся, что заголовок всегда строка
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def get_events_page(self, url=None, changed_at=None):
        """Получение страницы событий (используется итератором)"""
        if not url:
            url = f"{self.base_url}/events/?changed_at={changed_at or '2000-01-01'}"

        try:
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching events page: {e}")
            raise

    def get_seats(self, event_id):
        # Провайдер требует слэш в конце!
        url = f"{self.base_url}/events/{event_id}/seats/"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching seats: {e}")
            raise

    def register(self, event_id, first_name, last_name, email, seat):
        # Провайдер требует слэш в конце!
        url = f"{self.base_url}/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        try:
            response = httpx.post(
                url, json=payload, headers=self.headers, timeout=10.0, follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during registration: {e}")
            raise

    def unregister(self, event_id, ticket_id):
        # Провайдер требует слэш в конце!
        url = f"{self.base_url}/events/{event_id}/unregister/"
        payload = {"ticket_id": str(ticket_id)}
        try:
            response = httpx.request(
                "DELETE",
                url,
                json=payload,
                headers=self.headers,
                timeout=10.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during unregistration: {e}")
            raise
