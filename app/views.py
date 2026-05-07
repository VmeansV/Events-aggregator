from django.shortcuts import get_object_or_404
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
