from django.contrib import admin

from .models import Contact, EmailOTP, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number', 'full_name', 'is_verified', 'is_staff', 'last_seen', 'date_joined')
    list_filter = ('is_verified', 'is_staff')
    search_fields = ('email', 'phone_number', 'full_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_seen')
    fields = (
        'email', 'password', 'phone_number', 'full_name', 'about', 'avatar',
        'is_verified', 'is_active', 'is_staff', 'is_superuser',
        'last_seen', 'date_joined',
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('owner', 'contact', 'created_at')
    search_fields = ('owner__email', 'contact__email')


admin.site.register(EmailOTP)
