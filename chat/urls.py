from django.urls import path

from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('room/<int:conversation_id>/', views.chat_room_view, name='chat_room'),
    path('room/<int:conversation_id>/upload/', views.upload_attachment, name='upload_attachment'),
]
