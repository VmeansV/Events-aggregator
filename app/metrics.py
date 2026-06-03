from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUEST_TOTAL = Counter(
    "http_requests_total", "Общее количество HTTP-запросов", ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Время обработки запросов",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


EVENTS_PROVIDER_REQUEST_TOTAL = Counter(
    "events_provider_requests_total",
    "Количество запросов к Events Provider",
    ["endpoint", "status"],
)

EVENTS_PROVIDER_DURATION = Histogram(
    "events_provider_request_duration_seconds",
    "Время ответа Events Provider",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


TICKETS_CREATED_TOTAL = Gauge("tickets_created_total", "Общее количество созданных билетов в БД")
TICKETS_CANCELLED_TOTAL = Gauge(
    "tickets_cancelled_total", "Общее количество отменённых билетов в БД"
)
EVENTS_TOTAL = Gauge("events_total", "Общее количество событий в БД")


CACHE_HITS_TOTAL = Counter("cache_hits_total", "Попадания в кеш (seats)")
CACHE_MISSES_TOTAL = Counter("cache_misses_total", "Промахи кеша (seats)")
