from .models import DjangoPlotlyDashDashapp, DjangoPlotlyDashStatelessapp


class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """ reading Django plotly models from default db """
        if model == DjangoPlotlyDashDashapp or model == DjangoPlotlyDashStatelessapp:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """ writing Django plotly models to default db """
        if model == DjangoPlotlyDashDashapp or model == DjangoPlotlyDashStatelessapp:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the Django plotly models only appear in the
        'default' database.
        """
        if app_label in ['django_plotly_dash',]:
            return db == 'default'
        return None