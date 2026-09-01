from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('set-profile/', views.set_profile_view, name='set_profile'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),
]
