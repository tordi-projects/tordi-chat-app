from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('set-profile/', views.set_profile_view, name='set_profile'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/phone/', views.update_phone_view, name='update_phone'),
    path('contacts/', views.contacts_list_view, name='contacts_list'),
    path('contacts/add/<int:user_id>/', views.add_contact_view, name='add_contact'),
    path('contacts/remove/<int:contact_id>/', views.remove_contact_view, name='remove_contact'),
    path('logout/', views.logout_view, name='logout'),
]
