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


class Event(models.Model):
    class Status(models.TextChoices):
        NEW = "new"
        PUBLISHED = "published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    event_time = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.NEW
    )
    number_of_visitors = models.IntegerField()
    changed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_at = MonitorField(monitor="status")
