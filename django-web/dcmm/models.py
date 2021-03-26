from djongo import models
from djongo.models import forms


class BlogContent(models.Model):
    comment = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    class Meta:
        abstract = True
# Create your models here.
