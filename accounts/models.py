import random
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    about = models.CharField(max_length=255, blank=True, default='Hey there! I am using Tordi.')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.full_name or self.phone_number

    def display_name(self):
        return self.full_name or self.phone_number

    # How long since the last poll/heartbeat before we consider someone
    # offline. Used instead of a toggled boolean, since there's no
    # persistent connection (polling, not WebSockets) to know the instant
    # someone closes the tab.
    ONLINE_THRESHOLD_SECONDS = 20

    def is_recently_active(self):
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < self.ONLINE_THRESHOLD_SECONDS

    def touch(self):
        """Call on every request that proves the user is actively using the app."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class OTP(models.Model):
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f'{self.phone_number} - {self.code}'
