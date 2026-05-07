from unittest.mock import MagicMock, patch

from app.client import EventsProviderClient


def test_get_events_page_success():
    client = EventsProviderClient()

    # Создаем фальшивый ответ от сервера
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"id": "1"}], "next": None}
    mock_response.status_code = 200

    # Подменяем реальный httpx.get на наш фальшивый
    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = client.get_events_page(changed_at="2000-01-01")

        # Проверяем:
        assert result["results"][0]["id"] == "1"
        # Проверяем, что в запрос ушел правильный заголовок (X-API-Key)
        args, kwargs = mock_get.call_args
        assert "X-API-Key" in kwargs["headers"]
