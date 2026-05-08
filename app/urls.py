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
)

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^api/health/?$", HealthCheckAPIView.as_view()),
    re_path(r"^api/sync/trigger/?$", SyncTriggerAPIView.as_view()),
    re_path(r"^api/events/?$", EventListAPIView.as_view()),
    re_path(r"^api/events/(?P<pk>[^/]+)/?$", EventDetailAPIView.as_view()),
    re_path(r"^api/events/(?P<event_id>[^/]+)/seats/?$", EventSeatsAPIView.as_view()),
    re_path(r"^api/tickets/?$", TicketAPIView.as_view()),
    re_path(r"^api/tickets/(?P<ticket_id>[^/]+)/?$", TicketDetailAPIView.as_view()),
]
