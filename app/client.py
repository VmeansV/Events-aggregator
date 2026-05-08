import logging
import os

import httpx

logger = logging.getLogger(__name__)


class EventsProviderClient:
    def __init__(self):
        # 1. Базовый URL провайдера из переменной окружения или внутренний адрес кластера
        self.base_url = os.getenv(
            "EVENTS_PROVIDER_URL",
            "http://student-system-events-provider-web.student-system-events-provider.svc:8000/api",
        ).rstrip("/")

        # 2. API-ключ (обязательно должен быть в .env или настройках LMS)
        self.api_key = os.getenv("LMS_API_KEY", "")

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
        """Получение списка свободных мест для события"""
        url = f"{self.base_url}/events/{event_id}/seats/"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching seats: {e}")
            raise

    def register(self, event_id, first_name, last_name, email, seat):
        """Регистрация на событие у провайдера"""
        url = f"{self.base_url}/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        try:
            response = httpx.post(url, json=payload, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during registration: {e}")
            raise

    def unregister(self, ticket_id, event_id=None):
        """
        Отмена регистрации.
        По ТЗ провайдера обычно требуется event_id в URL, но если мы его не знаем,
        пробуем универсальный путь /api/tickets/{id} или логируем ошибку.
        """
        if event_id:
            url = f"{self.base_url}/events/{event_id}/unregister/"
        else:
            # Если event_id не передан, пробуем прямой путь к тикету
            url = f"{self.base_url}/tickets/{ticket_id}/"

        payload = {"ticket_id": str(ticket_id)}

        try:
            # Для DELETE запроса в httpx используем именованный аргумент json
            response = httpx.request(
                "DELETE", url, json=payload, headers=self.headers, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error during unregistration for ticket {ticket_id}: {e}")
            raise
