from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CareerSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    input_data = models.JSONField()
    suggestion = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    citizenship = models.CharField(max_length=50, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    alt_email = models.EmailField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    pin_code = models.CharField(max_length=10, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
