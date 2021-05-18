from django.conf import settings
from djongo import models
# from djongo.models import forms


class Repository(models.Model):
    github_repository = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    any_repository = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='co_authored_by')

# Respecify the Dash plotly models
class DjangoPlotlyDashDashapp(models.Model):
    instance_name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=110)
    base_state = models.TextField()
    creation = models.DateTimeField()
    update = models.DateTimeField()
    save_on_change = models.BooleanField()
    stateless_app = models.ForeignKey('DjangoPlotlyDashStatelessapp', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_plotly_dash_dashapp'


class DjangoPlotlyDashStatelessapp(models.Model):
    app_name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=110)

    class Meta:
        managed = False
        db_table = 'django_plotly_dash_statelessapp'

# DjangoPlotlyDashDashapp.objects = DjangoPlotlyDashDashapp.objects.using('default')
# DjangoPlotlyDashStatelessapp.objects = DjangoPlotlyDashStatelessapp.objects.using('default')
