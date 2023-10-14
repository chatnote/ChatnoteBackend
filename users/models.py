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

    google_access_token = models.TextField(blank=True, null=True, default=None)
    apple_access_token = models.TextField(blank=True, null=True, default=None)
    notion_access_token = models.TextField(blank=True, null=True, default=None)

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