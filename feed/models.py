# feed/models.py
from django.db import models


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    link_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title
