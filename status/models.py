from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Status(models.Model):
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.heic')
    VIDEO_EXTENSIONS = ('.mp4', '.webm', '.mov', '.ogg', '.mkv')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='statuses', on_delete=models.CASCADE)
    text = models.CharField(max_length=700, blank=True)
    media = models.FileField(upload_to='status_media/', blank=True, null=True)
    background_color = models.CharField(max_length=20, default='#5B4FE9')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def media_kind(self):
        if not self.media:
            return None
        name = self.media.name.lower()
        if name.endswith(self.IMAGE_EXTENSIONS):
            return 'image'
        if name.endswith(self.VIDEO_EXTENSIONS):
            return 'video'
        return 'file'

    def __str__(self):
        return f'{self.user} @ {self.created_at:%Y-%m-%d %H:%M}'


class StatusView(models.Model):
    status = models.ForeignKey(Status, related_name='views', on_delete=models.CASCADE)
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('status', 'viewer')

    def __str__(self):
        return f'{self.viewer} viewed {self.status_id}'
