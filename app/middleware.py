import time

from django.urls import resolve

from app.metrics import HTTP_REQUEST_DURATION, HTTP_REQUEST_TOTAL


class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/metrics":
            return self.get_response(request)

        try:
            match = resolve(request.path)
            endpoint = match.route
        except Exception:
            endpoint = request.path

        start_time = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start_time

        HTTP_REQUEST_TOTAL.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()

        HTTP_REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(duration)

        return response
