from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=20)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(Author, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
