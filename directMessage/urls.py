from django.urls import path

from . import views

urlpatterns = [
    path('', views.inbox, name='dm_inbox'),
]
