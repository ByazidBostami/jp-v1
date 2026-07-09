from django.contrib import admin
from .models import User, Role, Permission, AuditLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "account_status", "created_at")
    list_filter = ("account_status", "role")
    search_fields = ("email", "mobile")

admin.site.register(Role)
admin.site.register(Permission)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "entity_type", "entity_id")
    list_filter = ("action",)
    search_fields = ("action", "entity_type")
