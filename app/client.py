import logging
import os

import httpx

logger = logging.getLogger(__name__)


class EventsProviderClient:
    def __init__(self):
        # 1. Берем базовый URL из переменных окружения.
        # Если переменной нет, используем внутренний адрес из задания.
        self.base_url = os.getenv(
            "EVENTS_PROVIDER_URL",
            "http://student-system-events-provider-web.student-system-events-provider.svc:8000/api",
        ).rstrip("/")

        # 2. API-ключ для доступа к Провайдеру
        self.api_key = os.getenv("LMS_API_KEY", "ваш_дефолтный_ключ")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def get_events_page(self, url=None, changed_at=None):
        """Скачивает одну страницу событий (GET /api/events/)"""
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
        """Получает список мест (GET /api/events/{id}/seats/)"""
        url = f"{self.base_url}/events/{event_id}/seats/"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching seats: {e}")
            raise

    def register(self, event_id, first_name, last_name, email, seat):
        """Регистрация на событие (POST /api/events/{id}/register/)"""
        url = f"{self.base_url}/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        try:
            response = httpx.post(url, json=payload, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during registration: {e}")
            raise

    def unregister(self, event_id, ticket_id):
        """
        Отмена регистрации (DELETE /api/events/{id}/unregister/)
        Согласно ТЗ провайдера, ticket_id передается в теле запроса.
        """
        url = f"{self.base_url}/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        try:
            # В httpx.delete для передачи тела используется аргумент content или json
            response = httpx.request(
                "DELETE", url, json=payload, headers=self.headers, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during unregistration: {e}")
            raise
