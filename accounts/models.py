import random
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)

    # Optional — added later from Settings, purely so other users can find
    # this account by number. Not used for login and not SMS-verified.
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    full_name = models.CharField(max_length=150, blank=True)
    about = models.CharField(max_length=255, blank=True, default='Hey there! I am using Tordi.')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # A user counts as "online" if they've loaded a page or been polled
    # within this many seconds. Computed on the fly (see is_recently_active)
    # rather than stored, since polling has no persistent connection to
    # detect a closed tab.
    ONLINE_THRESHOLD_SECONDS = 20

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.full_name or self.email

    def display_name(self):
        return self.full_name or self.email.split('@')[0]

    def is_recently_active(self):
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < self.ONLINE_THRESHOLD_SECONDS

    def touch(self):
        """Heartbeat — called on page loads/polls so presence stays accurate."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class EmailOTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f'{self.email} - {self.code}'


class Contact(models.Model):
    """
    owner has added `contact` to their address book. This is one-directional
    by design: it doubles as the Tordi Status audience list — owner posts a
    status, and only the people owner has added here can view it.
    """
    owner = models.ForeignKey(User, related_name='my_contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(User, related_name='added_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'contact')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.owner} -> {self.contact}'
