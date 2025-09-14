from django.contrib.auth.models import AbstractUser
from django.db import models


class InstagramMessage(models.Model):
    sender = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)   # not all webhooks have text (some are attachments)
    ig_message_id = models.CharField(max_length=255, unique=True)  # prevent duplicates
    created_at = models.DateTimeField()  # actual IG timestamp
    received_at = models.DateTimeField(auto_now_add=True)  # when saved in DB

    def __str__(self):
        return f"{self.sender}: {self.text[:30] if self.text else '[media]'}"


class User(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_COUNSELOR = 'COUNSELOR'
    ROLE_NUTRITIONIST = 'NUTRITIONIST'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_COUNSELOR, 'Counselor'),
        (ROLE_NUTRITIONIST, 'Nutritionist'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_COUNSELOR)

    def __str__(self):
        return f"{self.username} ({self.role})"
