import os

import httpx


class EventsProviderClient:
    def __init__(self):
        self.base_url = "http://events-provider-url/api"
        self.api_key = os.getenv("LMS_API_KEY")
        self.headers = {"X-API-Key": self.api_key}

    def get_events_page(self, url=None, changed_at=None):
        """Скачивает одну страницу событий"""
        if not url:
            url = f"{self.base_url}/events/?changed_at={changed_at or '2000-01-01'}"

        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def register(self, event_id, first_name, last_name, email, seat):
        """Метод для регистрации на событие у провайдера"""
        url = f"{self.base_url}/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        response = httpx.post(url, json=payload, headers=self.headers)
        return response.json()
