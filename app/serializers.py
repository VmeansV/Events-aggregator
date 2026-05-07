from rest_framework import serializers

from app.models import Event, Place


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "city", "name", "address", "seats_pattern", "changed_at", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "place",
            "event_time",
            "registration_deadline",
            "status",
            "number_of_visitors",
            "changed_at",
            "created_at",
            "status_changed_at",
        ]
