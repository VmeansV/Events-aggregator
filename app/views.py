import httpx
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Event
from app.pagination import EventPagination
from app.serializers import EventSerializer
from app.services import (
    cancel_ticket_registration,
    create_ticket_registration,
    get_event_seats_with_cache,
    sync_events_from_provider,
)


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


class EventSeatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_id):
        try:
            result = get_event_seats_with_cache(event_id)
            return Response(result, status=200)
        except Http404:
            raise
        except httpx.HTTPStatusError as e:
            return Response({"detail": "Not found on provider"}, status=e.response.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class TicketAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Вся логика теперь внутри одной функции
            result = create_ticket_registration(request.data)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Здесь можно добавить более детальную обработку ошибок
            return Response({"error": str(e)}, status=400)


class TicketDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, ticket_id):
        try:
            success, error_message = cancel_ticket_registration(ticket_id)
            if not success:
                return Response({"detail": error_message}, status=404)

            return Response({"success": True}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
