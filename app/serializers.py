from rest_framework import serializers

from app.models import Event, Place, Registration


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name", "city", "address", "seats_pattern"]


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
        ]


class RegistrationSerializer(serializers.ModelSerializer):
    ticket_id = serializers.UUIDField(source="id")

    class Meta:
        model = Registration
        fields = ["ticket_id", "event_id", "seat", "first_name", "last_name", "email", "status"]
