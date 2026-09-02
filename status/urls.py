from django.urls import path

from . import views

urlpatterns = [
    path('mine/', views.my_status_view, name='my_status'),
    path('create/', views.create_status_view, name='create_status'),
    path('<int:status_id>/delete/', views.delete_status_view, name='delete_status'),
    path('<int:status_id>/viewed/', views.mark_status_viewed, name='mark_status_viewed'),
    path('<int:user_id>/', views.view_status, name='view_status'),
]
