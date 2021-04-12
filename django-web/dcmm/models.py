from django.conf import settings
from djongo import models
# from djongo.models import forms


class Repository(models.Model):
    github_repository = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    any_repository = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='co_authored_by')
