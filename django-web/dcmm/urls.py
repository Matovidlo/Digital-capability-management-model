from django.urls import path, re_path

from dcmm import views

urlpatterns = [
    path('', views.index, name='index'),
    # Matches any html file
    path('settings.html', views.settings, name='settings'),
    path('profile.html', views.pages, name='profile'),
    path('gathering.html', views.gathering, name='gathering'),
    path('visualisations.html', views.visualisations, name='visualisations'),
    path('tables.html?username=<str:username>', views.tables, name='tables')
]