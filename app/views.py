from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app.client import EventsProviderClient
from app.models import Event, Registration
from app.pagination import EventPagination
from app.serializers import EventSerializer
from app.services import sync_events_from_provider

# from app.permissions import HasLMSAPIKey


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=200)


class SyncTriggerAPIView(APIView):
    def post(self, request):
        try:
            count = sync_events_from_provider()
            return Response({"status": "success", "synced_count": count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EventListAPIView(generics.ListAPIView):
    queryset = Event.objects.all().select_related("place").order_by("event_time")
    serializer_class = EventSerializer
    pagination_class = EventPagination
    # permission_classes = [HasLMSAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()

        date_from = self.request.query_params.get("date_from")

        if date_from:
            queryset = queryset.filter(event_time__date__gte=date_from)

        return queryset

    def list(self, request, *args, **kwargs):
        change_at_param = self.request.query_params.get("change_at")

        if not change_at_param:
            raise serializers.ValidationError({"changed_at": ["This parameter is required."]})

        if parse_date(change_at_param) is None:
            raise serializers.ValidationError({"changed_at": ["Enter a valid date."]})

        return super().list(request, *args, **kwargs)


class EventSeatsAPIView(APIView):
    # permission_classes = [HasLMSAPIKey]

    def get(self, request, event_id):
        cache_key = f"seats_{event_id}"
        cached_seats = cache.get(cache_key)

        if cached_seats:
            return Response({"event_id": event_id, "available_seats": cached_seats})

        client = EventsProviderClient()
        try:
            remote_data = client.get_seats(event_id)
            available_seats = remote_data.get("seats", [])

            cache.set(cache_key, available_seats, timeout=30)

            return Response({"event_id": event_id, "available_seats": available_seats})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class RegisterEventAPIView(APIView):
    # permission_classes = [HasLMSAPIKey]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        data = request.data

        if event.statut != "published":
            return Response(
                {"detail": "Registration is only allowed for published events."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now > event.registration_deadline:
            return Response(
                {"detail": "Registration deadline has passed."}, status=status.HTTP_400_BAD_REQUEST
            )

        seat = data.get("seat")

        if seat not in event.place.get_all_seats():
            return Response(
                {"detail": f"Seat {seat} does not exist in this place."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Registration.objects.filter(event=event, seat=seat).exists():
            return Response(
                ["This ticket is not available (already sold)."], status=status.HTTP_400_BAD_REQUEST
            )

        registration = Registration.objects.create(
            event=event,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            seat=seat,
        )

        return Response({"ticket_id": registration.id}, status=status.HTTP_201_CREATED)


class UnregisterEventAPIView(APIView):
    # permission_classes = [HasLMSAPIKey]

    def delete(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        ticket_id = request.data.get("ticket_id")

        if not ticket_id:
            return Response(
                {"detail": "ticket_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        registration = Registration.objects.filter(ticket_id=ticket_id, event=event).first()

        if not registration:
            return Response({"detail": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

        if timezone.now > event.event_time:
            return Response(
                {"detail": "Cannot cancel registration for a past event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration.delete()

        return Response({"success": True}, status=status.HTTP_200_OK)


class EventDetailAPIView(generics.RetrieveAPIView):
    queryset = Event.objects.all().select_related("place")
    serializer_class = EventSerializer


class TicketAPIView(APIView):
    def post(self, request):
        client = EventsProviderClient()
        try:
            remote_response = client.register(
                event_id=request.data.get("event_id"),
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                email=request.data.get("email"),
                seat=request.data.get("seat"),
            )
            return Response(remote_response, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class TicketDetailAPIView(APIView):
    def delete(self, request, ticket_id):
        client = EventsProviderClient()
        try:
            _result = client.unregister(ticket_id)
            return Response({"success": True}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
