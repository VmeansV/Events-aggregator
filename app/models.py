import re
import uuid

from django.db import models
from model_utils.fields import MonitorField


class User(models.Model):
    pass


class Place(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    seats_pattern = models.CharField(max_length=255)
    changed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_all_seats(self):
        """Парсит seats_pattern и возвращает полный список мест"""
        all_seats = []

        parts = self.seats_pattern.split(",")  # "A1-5,B1-10" -> ["A1-5", "B1-10"]

        for part in parts:
            match = re.match(r"([A-Z])(\d+)-(\d+)", part.strip())  # "A1-5"
            if match:
                section = match.group(1)  # "A"
                start = int(match.group(2))  # 1
                end = int(match.group(3))  # 5

                for i in range(start, end + 1):
                    all_seats.append(f"{section}{i}")

        return all_seats


class Event(models.Model):
    class Status(models.TextChoices):
        NEW = "new"
        PUBLISHED = "published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    event_time = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.NEW)
    number_of_visitors = models.IntegerField()
    changed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_at = MonitorField(monitor="status")


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "seat")
