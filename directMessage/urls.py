from django.urls import path

from . import views

urlpatterns = [
    path('', views.inbox, name='dm_inbox'),
    path('professors/', views.professor_list, name='professor_list'),
    path('professors/<int:professor_id>/start/', views.conversation_start, name='conversation_start'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('<int:conversation_id>/messages/', views.message_create, name='message_create'),
]
