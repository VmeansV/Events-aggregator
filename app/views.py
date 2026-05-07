from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Event, Registration
from app.pagination import EventCursorPagination
from app.permissions import HasLMSAPIKey
from app.serializers import EventSerializer


class EventListAPIView(generics.ListAPIView):
    serializer_class = EventSerializer
    pagination_class = EventCursorPagination
    permission_classes = [HasLMSAPIKey]

    def get_queryset(self):
        queryset = Event.objects.all().select_related("place")
        change_at_param = self.request.query_params.get("change_at")

        if change_at_param:
            date_value = parse_date(change_at_param)

            if date_value:
                return queryset.filter(change_at__date__gte=date_value)
            else:
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        change_at_param = self.request.query_params.get("change_at")

        if not change_at_param:
            raise serializers.ValidationError({"changed_at": ["This parameter is required."]})

        if parse_date(change_at_param) is None:
            raise serializers.ValidationError({"changed_at": ["Enter a valid date."]})

        return super().list(request, *args, **kwargs)


class EventSeatsAPIView(APIView):
    permission_classes = [HasLMSAPIKey]

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if event.status != "published":
            return Response(
                "UnexpectedEventStatus: Event is not published for registration.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type="text/html",
            )

        all_seats = event.place.get_all_seats()

        occupied_seats = Registration.objects.filter(event=event).values_list("seat", flat=True)

        free_seats = [seat for seat in all_seats if seat not in occupied_seats]

        free_seats.sort()

        return Response({"seats": free_seats})


class RegisterEventAPIView(APIView):
    permission_classes = [HasLMSAPIKey]

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
    permission_classes = [HasLMSAPIKey]

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
