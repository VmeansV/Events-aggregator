class EventsPaginator:
    def __init__(self, client, changed_at=None):
        self.client = client
        self.changed_at = changed_at
        self.next_url = None
        self.first_request = True
        self.current_results = []

    def __iter__(self):
        return self

    def __next__(self):
        # Если в текущем списке еще есть события, отдаем следующее
        if self.current_results:
            return self.current_results.pop(0)

        # Если страниц больше нет, останавливаемся
        if not self.first_request and not self.next_url:
            raise StopIteration

        # Загружаем следующую страницу через клиента
        data = self.client.get_events_page(url=self.next_url, changed_at=self.changed_at)
        self.first_request = False
        self.next_url = data.get("next")
        self.current_results = data.get("results", [])

        if not self.current_results:
            raise StopIteration

        return self.current_results.pop(0)
