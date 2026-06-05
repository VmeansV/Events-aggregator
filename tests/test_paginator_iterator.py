import unittest
from unittest.mock import MagicMock

from app.paginator import EventsPaginator


class TestEventsPaginatorIterator(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()

    def test_iterator_multi_page(self):
        page1 = {"results": [{"id": "1", "name": "Event 1"}], "next": "http://api.com/page2"}
        page2 = {"results": [{"id": "2", "name": "Event 2"}], "next": None}
        self.mock_client.get_events_page.side_effect = [page1, page2]

        paginator = EventsPaginator(client=self.mock_client)
        results = list(paginator)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Event 1")
        self.assertEqual(results[1]["name"], "Event 2")
        self.assertEqual(self.mock_client.get_events_page.call_count, 2)

    def test_iterator_empty_response(self):
        self.mock_client.get_events_page.return_value = {"results": [], "next": None}

        paginator = EventsPaginator(client=self.mock_client)
        results = list(paginator)

        self.assertEqual(len(results), 0)
        self.mock_client.get_events_page.assert_called_once()

    def test_iterator_stops_correctly(self):
        self.mock_client.get_events_page.return_value = {"results": [{"id": "1"}], "next": None}

        paginator = EventsPaginator(client=self.mock_client)
        iterator = iter(paginator)

        item = next(iterator)
        self.assertEqual(item["id"], "1")

        with self.assertRaises(StopIteration):
            next(iterator)
