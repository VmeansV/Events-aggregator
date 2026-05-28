import re
import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone
from model_utils.fields import MonitorField


class SyncMetadata(models.Model):
    last_sync_time = models.DateTimeField(auto_now=True)
    last_changed_at = models.DateTimeField(default=timezone.make_aware(datetime(2000, 1, 1)))
    status = models.CharField(max_length=20, default="never_synced")


class Place(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    place = models.ForeignKey("Place", on_delete=models.CASCADE)
    event_time = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.NEW)
    number_of_visitors = models.IntegerField()
    changed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_at = MonitorField(monitor="status")


class Registration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=255, null=False)
    seat = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=255, null=True, blank=True, unique=True)

    class Meta:
        unique_together = ("event", "seat")


class OutboxMessage(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSED = "processed"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
