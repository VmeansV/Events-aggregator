from django.utils.dateparse import parse_date
from rest_framework import generics, serializers

from app.models import Event
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
