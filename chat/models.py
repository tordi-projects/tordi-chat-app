from django.conf import settings
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=150, blank=True)
    group_avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.group_name if self.is_group else f'Conversation {self.id}'

    def other_participant(self, user):
        if self.is_group:
            return None
        return self.participants.exclude(id=user.id).first()

    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.sender}: {self.text[:30]}'

    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.heic')
    VIDEO_EXTENSIONS = ('.mp4', '.webm', '.mov', '.ogg', '.mkv')

    def attachment_kind(self):
        """'image', 'video', 'file', or None — computed from the filename,
        so no extra DB column/migration is needed."""
        if not self.attachment:
            return None
        name = self.attachment.name.lower()
        if name.endswith(self.IMAGE_EXTENSIONS):
            return 'image'
        if name.endswith(self.VIDEO_EXTENSIONS):
            return 'video'
        return 'file'
