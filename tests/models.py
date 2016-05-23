from django.db import models
from django.utils import timezone


class Post(models.Model):
    name = models.CharField(max_length=20)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
