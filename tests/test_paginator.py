from unittest.mock import MagicMock

from app.paginator import EventsPaginator


def test_paginator_iteration():
    # Создаем фальшивого клиента
    mock_client = MagicMock()

    # Имитируем, что на первой странице 1 событие и есть ссылка на вторую
    page1 = {"results": [{"name": "Event 1"}], "next": "url_page_2"}
    # На второй странице 1 событие и ссылок больше нет
    page2 = {"results": [{"name": "Event 2"}], "next": None}

    # Настраиваем клиента выдавать эти страницы по очереди
    mock_client.get_events_page.side_effect = [page1, page2]

    paginator = EventsPaginator(mock_client)
    events = list(paginator)  # Проходим по всему итератору

    # Проверяем:
    assert len(events) == 2
    assert events[0]["name"] == "Event 1"
    assert events[1]["name"] == "Event 2"
    assert mock_client.get_events_page.call_count == 2
