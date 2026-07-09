from django.contrib import admin
from .models import EmployerProfile

@admin.register(EmployerProfile)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("employer_code", "company_name_english", "approval_status")
    list_filter = ("approval_status",)
    search_fields = ("employer_code", "company_name_english")
