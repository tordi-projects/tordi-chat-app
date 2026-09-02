from django.contrib import admin

from .models import Status, StatusView


class StatusViewInline(admin.TabularInline):
    model = StatusView
    extra = 0
    readonly_fields = ('viewer', 'viewed_at')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    list_filter = ('user',)
    inlines = [StatusViewInline]
