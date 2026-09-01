from django.contrib import admin

from .models import OTP, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'is_verified', 'is_online', 'is_staff', 'date_joined')
    list_filter = ('is_verified', 'is_online', 'is_staff')
    search_fields = ('phone_number', 'full_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_seen')
    fields = (
        'phone_number', 'password', 'full_name', 'about', 'avatar',
        'is_verified', 'is_online', 'is_active', 'is_staff', 'is_superuser',
        'last_seen', 'date_joined',
    )


admin.site.register(OTP)
