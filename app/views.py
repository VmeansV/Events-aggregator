import httpx
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app.client import EventsProviderClient
from app.models import Event, Registration
from app.pagination import EventPagination
from app.serializers import EventSerializer
from app.services import sync_events_from_provider


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class SyncTriggerAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            count = sync_events_from_provider()
            return Response({"status": "success", "synced_count": count}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class EventListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EventSerializer
    pagination_class = EventPagination

    def get_queryset(self):
        queryset = Event.objects.all().select_related("place").order_by("event_time")
        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(event_time__date__gte=date_from)
        return queryset


class EventDetailAPIView(generics.RetrieveAPIView):
    queryset = Event.objects.all().select_related("place")
    serializer_class = EventSerializer
    permission_classes = [AllowAny]


# 5. Свободные места (с кэшированием)
class EventSeatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        cache_key = f"seats_{event.id}"
        cached_seats = cache.get(cache_key)

        if cached_seats:
            return Response(
                {"event_id": str(event.id), "available_seats": cached_seats}, status=200
            )

        client = EventsProviderClient()
        try:
            remote_data = client.get_seats(event.id)
            available_seats = remote_data.get("seats", [])

            cache.set(cache_key, available_seats, timeout=30)

            return Response(
                {"event_id": str(event.id), "available_seats": available_seats}, status=200
            )

        except httpx.HTTPStatusError as e:
            return Response({"detail": "Not found on provider"}, status=e.response.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class TicketAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        client = EventsProviderClient()
        event_id = request.data.get("event_id")
        seat = request.data.get("seat")

        try:
            remote_response = client.register(
                event_id=event_id,
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                email=request.data.get("email"),
                seat=seat,
            )

            provider_ticket_id = remote_response.get("ticket_id")

            Registration.objects.update_or_create(
                id=provider_ticket_id,
                defaults={
                    "event_id": event_id,
                    "seat": seat,
                    "first_name": request.data.get("first_name"),
                    "last_name": request.data.get("last_name"),
                    "email": request.data.get("email"),
                },
            )

            return Response(remote_response, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class TicketDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, ticket_id):
        reg = Registration.objects.filter(id=ticket_id).first()

        if not reg:
            return Response({"detail": "Ticket not found locally"}, status=404)

        client = EventsProviderClient()
        try:
            client.unregister(event_id=reg.event.id, ticket_id=ticket_id)

            reg.delete()
            return Response({"success": True}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
