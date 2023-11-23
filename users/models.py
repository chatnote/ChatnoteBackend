from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

# Create your models here.


class UserCustomManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class User(AbstractUser):
    first_name = None
    last_name = None
    username = None
    email = models.EmailField(verbose_name="email", max_length=255, unique=True)

    google_profile_image = models.TextField(blank=True, null=True, default=None)
    google_access_token = models.TextField(blank=True, null=True, default=None)
    apple_access_token = models.TextField(blank=True, null=True, default=None)
    notion_access_token = models.TextField(blank=True, null=True, default=None)

    gmail_access_token = models.TextField(blank=True, null=True, default=None)
    gmail_refresh_token = models.TextField(blank=True, null=True, default=None)
    gmail_google_user_id = models.CharField(max_length=255, blank=True, null=True, default=None)
    gmail_email = models.CharField(max_length=255, blank=True, null=True, default=None)

    google_drive_access_token = models.TextField(blank=True, null=True, default=None)
    google_drive_refresh_token = models.TextField(blank=True, null=True, default=None)
    google_drive_google_user_id = models.CharField(max_length=255, blank=True, null=True, default=None)
    google_drive_email = models.CharField(max_length=255, blank=True, null=True, default=None)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserCustomManager()

    def __str__(self):
        return f"{self.id} {self.email}"

    @classmethod
    def validate(cls, user) -> bool:
        try:
            cls.objects.get(email=user.email)
            return True
        except cls.DoesNotExist:
            return False
