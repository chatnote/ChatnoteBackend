from datetime import datetime

from django.db import models

# Create your models here.


class SoftDeleteQueryset(models.QuerySet):
    def delete(self):
        return self.update(is_delete=True, deleted_at=datetime.now())

    def hard_delete(self):
        return self.delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQueryset(self.model, self._db).filter(is_delete=False)


class SoftDeleteModel(models.Model):
    is_delete = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True
