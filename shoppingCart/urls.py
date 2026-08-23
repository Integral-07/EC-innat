from django.urls import path

from . import views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('items/<int:item_id>/', views.cart_item_create, name='cart_item_create'),
    path('items/<int:item_id>/delete/', views.cart_item_delete, name='cart_item_delete'),
    path('checkout/', views.cart_checkout, name='cart_checkout'),
]
