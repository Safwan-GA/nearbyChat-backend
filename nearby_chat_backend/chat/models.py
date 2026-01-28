from django.db import models

class Room(models.Model):
    firebase_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    creator_id = models.CharField(max_length=255)
    radius_meters = models.IntegerField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, default="active")

class Message(models.Model):
    firebase_id = models.CharField(max_length=255, unique=True)
    room_id = models.CharField(max_length=255)
    sender_id = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)
