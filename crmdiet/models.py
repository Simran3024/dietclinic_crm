from django.contrib.auth.models import AbstractUser
from django.db import models

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
