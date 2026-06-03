from django.contrib import admin
from django.urls import path, re_path  # Добавь re_path

from app.views import (
    EventDetailAPIView,
    EventListAPIView,
    EventSeatsAPIView,
    HealthCheckAPIView,
    SyncTriggerAPIView,
    TicketAPIView,
    TicketDetailAPIView,
    metrics_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^metrics/?$", metrics_view, name="metrics"),
    re_path(r"^api/health/?$", HealthCheckAPIView.as_view(), name="health-check"),
    re_path(r"^api/sync/trigger/?$", SyncTriggerAPIView.as_view(), name="sync-trigger"),
    re_path(r"^api/events/?$", EventListAPIView.as_view(), name="event-list"),
    re_path(r"^api/events/(?P<pk>[^/]+)/?$", EventDetailAPIView.as_view(), name="event-detail"),
    re_path(
        r"^api/events/(?P<event_id>[^/]+)/seats/?$", EventSeatsAPIView.as_view(), name="event-seats"
    ),
    re_path(r"^api/tickets/?$", TicketAPIView.as_view(), name="ticket-list"),
    re_path(
        r"^api/tickets/(?P<ticket_id>[^/]+)/?$", TicketDetailAPIView.as_view(), name="ticket-detail"
    ),
]
