from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.catalog_list, name='catalog_list'),
    path('details/<int:item_id>/', views.catalog_details, name='catalog_details'),
]