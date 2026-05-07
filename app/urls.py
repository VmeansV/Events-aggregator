"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

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
    path("api/health", HealthCheckAPIView.as_view()),
    path("api/sync/trigger", SyncTriggerAPIView.as_view()),
    path("api/events", EventListAPIView.as_view()),
    path("api/events/<uuid:pk>", EventDetailAPIView.as_view()),
    path("api/events/<uuid:event_id>/seats", EventSeatsAPIView.as_view()),
    path("api/tickets", TicketAPIView.as_view()),
    path("api/tickets/<uuid:ticket_id>", TicketDetailAPIView.as_view()),
]
